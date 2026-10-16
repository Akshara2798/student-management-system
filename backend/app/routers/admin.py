import hmac                                                                                                 # safe constant-time string comparison (prevents timing attacks)
from datetime import datetime, timezone                                                                     # date/time tools for token expiry

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status                            # FastAPI building blocks
from sqlalchemy.exc import IntegrityError                                                                   # raised when a DB unique constraint is violated
from sqlalchemy.orm import Session                                                                          # type for the database session

from app.auth import rate_limit                                                                             # helper that blocks too many repeated attempts
from app.auth.dependencies import get_current_admin                                                         # dependency that returns the logged-in admin
from app.auth.security import (                                                                             # security helpers
    DUMMY_HASH,                                                                                             # fake hash used so unknown emails still take the same time
    create_access_token,                                                                                    # builds a signed JWT for the admin
    decode_access_token,                                                                                    # reads and verifies a JWT
    hash_password,                                                                                          # turns a plain password into a bcrypt hash
    utcnow,                                                                                                 # current UTC time (naive, matches DB columns)
    verify_password,                                                                                        # compares plain password with stored hash
)
from app.config import (                                                                                    # settings loaded from the .env file
    ACCESS_TOKEN_EXPIRE_MINUTES,                                                                            # how long the login token lives
    ADMIN_INVITE_CODE,                                                                                      # secret code required to register an admin
    COOKIE_NAME,                                                                                            # name of the auth cookie
    COOKIE_SAMESITE,                                                                                        # cookie SameSite policy (CSRF protection)
    COOKIE_SECURE,                                                                                          # send cookie over HTTPS only when True
)
from app.database import get_db                                                                             # dependency that gives a DB session per request
from app.Model.admin import Admin, RevokedToken                                                             # DB models for admins and blacklisted tokens
from app.schemas.admin import AdminLogin, AdminRegister, AdminResponse, AuthResponse                        # request/response schemas

router = APIRouter(prefix="/admin", tags=["Admin"])                                                         # groups all routes under /admin in the API docs


def _client_ip(request: Request) -> str:                                                                    # returns the caller's IP address
    """
    WHY WE USE THIS FUNCTION:
    - Rate limiting needs to know WHO is calling, and the IP is the key.
    - request.client can be None (e.g. some proxies/tests), so we fall back
      to "unknown" instead of crashing with an AttributeError.
    - The leading underscore means it is a private helper, not a route.
    """
    return request.client.host if request.client else "unknown"                                             # IP if available, otherwise "unknown"


# REGISTER ------------------------------------------------------------------
@router.post("/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)                # POST /admin/register -> 201
def register_admin(data: AdminRegister, request: Request, db: Session = Depends(get_db)):                   # create a new admin account
    """
    WHY WE USE THIS FUNCTION:
    - Creates a new admin, but only for people holding the secret invite code,
      so nobody can make themselves an admin just by calling the API.
    - Rate limits failed attempts so the invite code cannot be brute-forced.
    - Checks for duplicate emails twice (query + IntegrityError) to be safe
      even when two requests arrive at the same instant.
    - Stores only a bcrypt hash, never the plain password.
    """

    # Nobody becomes an admin just by submitting the form:
    # a valid invitation code (from backend/.env) is required.
    if not ADMIN_INVITE_CODE:                                                                               # no code configured on the server
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin registration is disabled.")                   # registration turned off

    limiter_key = f"register:{_client_ip(request)}"                                                         # unique counter key per IP for registration
    rate_limit.check(limiter_key)                                                                           # block the request if this IP failed too many times

    if not hmac.compare_digest(                                                                             # constant-time compare of submitted vs real invite code
        data.invite_code.encode("utf-8"), ADMIN_INVITE_CODE.encode("utf-8")                                 # both converted to bytes for comparison
    ):
        rate_limit.fail(limiter_key)                                                                        # record a failed attempt for this IP
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid invitation code.")                          # wrong code -> 403

    if db.query(Admin).filter(Admin.email == data.email).first():                                           # is this email already registered?
        raise HTTPException(status.HTTP_409_CONFLICT, "An admin with this email already exists.")           # duplicate -> 409

    admin = Admin(                                                                                          # build the new admin object
        full_name=data.full_name,                                                                           # name from the form
        email=data.email,                                                                                   # email from the form (already lowercase)
        hashed_password=hash_password(data.password),                                                       # store the hash, never the plain password
        role="admin",                                                                                       # fixed role for this endpoint
    )
    db.add(admin)                                                                                           # stage the new admin for saving
    try:                                                                                                    # attempt to save
        db.commit()                                                                                         # write to the database
    except IntegrityError:  # two requests with the same email at the same moment
        db.rollback()                                                                                       # undo the failed transaction
        raise HTTPException(status.HTTP_409_CONFLICT, "An admin with this email already exists.")           # duplicate -> 409
    db.refresh(admin)                                                                                       # reload the admin to get its new id
    return admin                                                                                            # FastAPI converts it using AdminResponse (no password hash)


# LOGIN ---------------------------------------------------------------------
@router.post("/login", response_model=AuthResponse)                                                         # POST /admin/login
def login_admin(                                                                                            # authenticate an admin
    data: AdminLogin,                                                                                       # email + password from the request body
    request: Request,                                                                                       # used to read the client IP
    response: Response,                                                                                     # used to set the cookie
    db: Session = Depends(get_db),                                                                          # database session
):
    """
    WHY WE USE THIS FUNCTION:
    - Verifies the admin's credentials and logs them in by setting a cookie.
    - Always runs one bcrypt check (even for unknown emails) so response time
      does not reveal whether an email exists.
    - Uses one generic error message so attackers cannot tell which part
      (email or password) was wrong.
    - Rate limits by IP + email to slow down password guessing.
    - Stores the JWT in an HttpOnly cookie so JavaScript (XSS) cannot steal it.
    """
    limiter_key = f"login:{_client_ip(request)}:{data.email}"                                               # counter key per IP and email
    rate_limit.check(limiter_key)                                                                           # block if too many failed logins

    admin = db.query(Admin).filter(Admin.email == data.email).first()                                       # look up the admin by email

    # Always run one bcrypt check, even for unknown emails (same response time)
    password_ok = verify_password(data.password, admin.hashed_password if admin else DUMMY_HASH)            # real or dummy hash check

    if admin is None or not password_ok or not admin.is_active:                                             # unknown email, wrong password, or disabled account
        rate_limit.fail(limiter_key)                                                                        # count this failed attempt
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password.")                     # generic 401 message

    if admin.role != "admin":                                                                               # only real admins may log in here
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")                            # wrong role -> 403

    rate_limit.reset(limiter_key)                                                                           # successful login clears the failure counter

    token, _jti, _expires_at = create_access_token(admin.id, admin.role)                                    # make the JWT (only the token is needed here)

    # HttpOnly: JavaScript cannot read the cookie, so XSS cannot steal the token
    response.set_cookie(                                                                                    # attach the token cookie to the response
        key=COOKIE_NAME,                                                                                    # cookie name
        value=token,                                                                                        # the JWT string
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,                                                           # lifetime in seconds
        httponly=True,                                                                                      # hide the cookie from JavaScript
        secure=COOKIE_SECURE,                                                                               # HTTPS only (when enabled in config)
        samesite=COOKIE_SAMESITE,                                                                           # limits cross-site sending (CSRF protection)
        path="/",                                                                                           # cookie is sent for every route
    )
    return {"message": "Login successful.", "admin": admin}                                                 # matches the AuthResponse schema


# LOGOUT --------------------------------------------------------------------
@router.post("/logout")                                                                                     # POST /admin/logout
def logout_admin(request: Request, response: Response, db: Session = Depends(get_db)):                      # log the admin out
    """
    WHY WE USE THIS FUNCTION:
    - Deleting the cookie alone is not enough: a copied token would still work.
    - So we also add the token's id (jti) to a revoked-tokens table, which the
      auth dependency checks on every request.
    - Expired revoked tokens are cleaned up so the table does not grow forever.
    """

    token = request.cookies.get(COOKIE_NAME)                                                                # read the token from the cookie
    payload = decode_access_token(token) if token else None                                                 # decode it (None if missing or invalid)

    # Revoke the token on the server so a copied token can no longer be used
    if payload and db.get(RevokedToken, payload["jti"]) is None:                                            # valid token not already revoked
        db.add(                                                                                             # stage a revoked-token record
            RevokedToken(                                                                                   # blacklist entry
                jti=payload["jti"],                                                                         # unique id of the token
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None),    # token expiry as naive UTC
            )
        )
        db.commit()                                                                                         # save the blacklist entry

    # Housekeeping: revoked tokens that have expired anyway are not needed
    db.query(RevokedToken).filter(RevokedToken.expires_at < utcnow()).delete()                              # remove already-expired entries
    db.commit()                                                                                             # save the cleanup

    response.delete_cookie(                                                                                 # tell the browser to remove the cookie
        key=COOKIE_NAME,                                                                                    # same name as when it was set
        path="/",                                                                                           # same path as when it was set
        httponly=True,                                                                                      # same flags so the browser matches the cookie
        secure=COOKIE_SECURE,                                                                               # same secure flag
        samesite=COOKIE_SAMESITE,                                                                           # same SameSite policy
    )
    return {"message": "You have been logged out successfully."}                                            # confirmation message


# CURRENT ADMIN -------------------------------------------------------------
@router.get("/me", response_model=AdminResponse)                                                            # GET /admin/me
def read_current_admin(admin: Admin = Depends(get_current_admin)):                                          # return the logged-in admin
    """
    WHY WE USE THIS FUNCTION:
    - Lets the frontend ask "who am I?" on page load to check if the user is
      still logged in and to show their name/role.
    - get_current_admin does the real work (cookie, token, revoked check),
      so this route stays tiny and is automatically protected.
    """
    return admin                                                                                            # serialized with AdminResponse (no password hash)