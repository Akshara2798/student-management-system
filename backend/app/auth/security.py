"""Password hashing and JWT helpers."""
import uuid                                                                             # generates random unique ids (used for the token id)
from datetime import datetime, timedelta, timezone                                      # date/time tools for token expiry

import bcrypt                                                                           # library for hashing and checking passwords
import jwt                                                                              # PyJWT library for creating and reading tokens

from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY               # token settings from the .env file


def utcnow() -> datetime:                                                               # returns the current UTC time without timezone info
    """
    Naive UTC datetime (MySQL DATETIME columns are naive).

    WHY WE USE THIS FUNCTION:
    - MySQL DATETIME columns do not store timezone info, so mixing naive and
      aware datetimes causes comparison errors.
    - One shared helper means the whole project uses the same time format
      (used for created_at defaults and expired-token cleanup).
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)                              # get UTC time, then drop the tzinfo to make it naive


# ---------- Passwords ----------
def hash_password(password: str) -> str:                                                # converts a plain password into a bcrypt hash
    """
    WHY WE USE THIS FUNCTION:
    - We never store plain passwords; if the database leaks, hashes are
      useless to attackers.
    - bcrypt adds a random salt and is intentionally slow, which makes
      brute-force guessing very expensive.
    - Returns a string so it can be saved in a normal String column.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")    # encode -> hash with new salt -> decode to str


def verify_password(password: str, hashed: str) -> bool:                                # checks a plain password against a stored hash
    """
    WHY WE USE THIS FUNCTION:
    - Hashes cannot be reversed, so at login we hash the typed password the
      same way and compare it with the stored hash.
    - Catches ValueError so a malformed or corrupted hash returns False
      instead of crashing the server with a 500 error.
    """
    try:                                                                                # attempt the comparison
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))         # True only if the password matches the hash
    except ValueError:                                                                  # raised when the stored hash is invalid
        return False                                                                    # treat a bad hash as a failed login


# Used when the email does not exist, so the response time is the same
# whether or not the account exists (prevents account enumeration by timing).
DUMMY_HASH = hash_password("not-a-real-password")                                       # fake hash, computed once when the module loads


# ---------- Tokens ----------
def create_access_token(admin_id: int, role: str):                                      # builds a signed JWT for a logged-in admin
    """
    Returns (token, jti, expires_at_naive_utc).

    WHY WE USE THIS FUNCTION:
    - After login, the client needs proof of identity; a signed JWT lets the
      server verify who the user is without storing a session.
    - The jti (unique token id) lets us revoke this exact token at logout.
    - exp makes the token stop working automatically after a set time.
    - Returns the expiry too, so callers can store it if needed.
    """
    jti = uuid.uuid4().hex                                                              # random unique id for this token
    expires_at = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)              # now + configured lifetime
    payload = {                                                                         # data stored inside the token (claims)
        "sub": str(admin_id),                                                           # subject: who the token belongs to (must be a string)
        "role": role,                                                                   # admin's role, for permission checks
        "jti": jti,                                                                     # token id, used for revocation
        "iat": datetime.now(timezone.utc),                                              # issued-at time
        "exp": expires_at.replace(tzinfo=timezone.utc),                                 # expiry time, marked as UTC so JWT reads it correctly
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)                        # sign the payload with the secret key
    return token, jti, expires_at                                                       # give back the token, its id, and its expiry


def decode_access_token(token: str):                                                    # reads and verifies a JWT
    """
    Returns the payload dict, or None if the token is invalid / expired.

    WHY WE USE THIS FUNCTION:
    - Checks the signature and expiry in one place, so no route has to repeat it.
    - Locks the allowed algorithm to ALGORITHM, which blocks tokens signed
      with a different (e.g. "none") algorithm.
    - Requires exp, sub and jti so tokens missing these claims are rejected.
    - Returns None instead of raising, so callers can simply treat None as
      "not logged in".
    """
    try:                                                                                # attempt to decode
        return jwt.decode(                                                              # verifies signature and expiry, then returns the payload
            token,                                                                      # the JWT string from the cookie
            SECRET_KEY,                                                                 # key used to verify the signature
            algorithms=[ALGORITHM],                                                     # only accept this algorithm
            options={"require": ["exp", "sub", "jti"]},                                 # these claims must exist in the token
        )
    except jwt.PyJWTError:                                                              # covers expired, tampered, or malformed tokens
        return None                                                                     # invalid token -> treat as not logged in