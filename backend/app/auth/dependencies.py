"""FastAPI dependency that protects routes: only a logged-in admin gets through."""
from fastapi import Depends, HTTPException, Request, status                                    # FastAPI tools for dependencies, errors and request access
from sqlalchemy.orm import Session                                                             # type for the database session

from app.auth.security import decode_access_token                                              # reads and verifies the JWT
from app.config import COOKIE_NAME                                                             # name of the cookie that holds the token
from app.database import get_db                                                                # dependency that gives a DB session per request
from app.Model.admin import Admin, RevokedToken                                                # DB models for admins and blacklisted tokens


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> Admin:               # returns the logged-in admin or raises an error
    """
    WHY WE USE THIS FUNCTION:
    - It is a FastAPI dependency: add Depends(get_current_admin) to any route
      and that route is protected, with no repeated login code.
    - Runs several checks in order (cookie, token, revoked, user, role) and
      stops at the first failure with a 401/403 error.
    - Reads the admin and role from the database on every request, so a
      disabled account or changed role takes effect immediately, even if
      the token itself is still valid.
    - Returns the Admin object so the route can use it directly.
    """
    token = request.cookies.get(COOKIE_NAME)                                                   # read the token from the cookie
    if not token:                                                                              # no cookie means not logged in
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.")                # 401: please log in

    payload = decode_access_token(token)                                                       # verify signature and expiry, get the claims
    if payload is None:                                                                        # token is invalid, tampered, or expired
        raise HTTPException(                                                                   # stop the request with an error
            status.HTTP_401_UNAUTHORIZED, "Your session has expired. Please sign in again."    # 401 with a friendly message
        )

    # Logout stores the token id (jti) here, so a copied token stops working
    if db.get(RevokedToken, payload["jti"]) is not None:                                       # is this token id in the blacklist?
        raise HTTPException(                                                                   # stop the request with an error
            status.HTTP_401_UNAUTHORIZED, "You have been signed out. Please sign in again."    # 401: token was revoked at logout
        )

    try:                                                                                       # attempt to read the admin id from the token
        admin_id = int(payload["sub"])                                                         # "sub" is stored as a string, convert it back to int
    except (TypeError, ValueError):                                                            # sub is missing the right format
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session.")                  # treat a bad id as an invalid session

    admin = db.get(Admin, admin_id)                                                            # look up the admin by primary key
    if admin is None or not admin.is_active:                                                   # admin was deleted or disabled
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session.")                  # 401: no valid account

    # Role is read from the database, never trusted from the token alone
    if admin.role != "admin":                                                                  # logged in, but not an admin
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")               # 403: authenticated but not allowed

    return admin                                                                               # all checks passed, hand the admin to the route