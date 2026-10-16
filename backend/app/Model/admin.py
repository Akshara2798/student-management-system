from sqlalchemy import Boolean, Column, DateTime, Integer, String           # column types used to define table fields

from app.auth.security import utcnow                                        # function that returns current UTC time (used as default)
from app.database import Base                                               # base class that all DB models inherit from


class Admin(Base):                                                          # model (table) that stores admin accounts
    """
    WHY WE USE THIS CLASS:
    - Maps the Python class to the "admins" table, so we can read and write
      admins with Python objects instead of raw SQL.
    - Stores only the hashed password, never the plain one.
    - role and is_active let us control who can log in and disable an
      account without deleting it.
    - created_at is filled automatically so we know when the account was made.
    """

    __tablename__ = "admins"                                                # actual table name in the database

    id = Column(Integer, primary_key=True, index=True)                      # unique row id, auto-increments, indexed for fast lookup
    full_name = Column(String(100), nullable=False)                         # admin's name, max 100 chars, required

    # unique=True is the database-level guard against duplicate registrations
    email = Column(String(255), unique=True, index=True, nullable=False)    # login email: unique, indexed, required

    hashed_password = Column(String(255), nullable=False)                   # bcrypt hash of the password, required
    role = Column(String(20), nullable=False, default="admin")              # permission level, defaults to "admin"
    is_active = Column(Boolean, nullable=False, default=True)               # False = account disabled, defaults to active
    created_at = Column(DateTime, nullable=False, default=utcnow)           # creation time, auto-set to current UTC time


class RevokedToken(Base):                                                   # model (table) that stores logged-out tokens
    """
    Tokens that were logged out. Rows are deleted after the token would have expired anyway.

    WHY WE USE THIS CLASS:
    - JWTs are stateless, so a token stays valid until it expires even after
      logout. This table is a blacklist that lets us cancel a token early.
    - We store only the token's id (jti), not the whole token, to keep it small.
    - expires_at lets us delete old rows later, because an expired token is
      invalid anyway and does not need to stay in the blacklist.
    """

    __tablename__ = "revoked_tokens"                                        # actual table name in the database

    jti = Column(String(64), primary_key=True)                              # unique id of the JWT, used as the primary key
    expires_at = Column(DateTime, nullable=False, index=True)               # when the token expires, indexed for fast cleanup queries