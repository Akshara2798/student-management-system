import re                                                                                           # regex module, used to check password patterns (lowercase, uppercase, digit)

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator       # pydantic tools for data validation


def validate_password_strength(value: str) -> str:                                                  # reusable helper that checks password rules
    """
    WHY WE USE THIS FUNCTION:
    - Keeps all password rules in ONE place, so register, reset-password,
      and change-password schemas can reuse it (DRY principle).
    - Rejects weak passwords before they ever reach the database.
    - Returns the value unchanged if valid, otherwise raises ValueError,
      which pydantic turns into a clean 422 error for the API client.
    """
    if len(value) < 8:                                                                              # too short passwords are easy to brute-force
        raise ValueError("Password must be at least 8 characters long")                             # error message sent to the client
    if len(value.encode("utf-8")) > 72:                                                             # bcrypt only uses the first 72 BYTES (not characters)
        raise ValueError("Password must be at most 72 bytes long")                                  # stops silent truncation by bcrypt
    if not re.search(r"[a-z]", value):                                                              # looks for at least one lowercase letter
        raise ValueError("Password must contain a lowercase letter")                                # fail if none found
    if not re.search(r"[A-Z]", value):                                                              # looks for at least one uppercase letter
        raise ValueError("Password must contain an uppercase letter")                               # fail if none found
    if not re.search(r"\d", value):                                                                 # \d matches any digit 0-9
        raise ValueError("Password must contain a number")                                          # fail if no digit found
    return value                                                                                    # password passed every rule, so return it


class AdminRegister(BaseModel):                                                                     # schema for the admin registration request body
    """
    WHY WE USE THIS CLASS:
    - Defines and validates the JSON the client sends when registering an admin.
    - FastAPI uses it automatically: bad data is rejected with a 422 error
      before your route code even runs.
    - Includes an invite_code so only people you invited can create admin accounts.
    """

    model_config = ConfigDict(str_strip_whitespace=True)                                            # auto-trim leading/trailing spaces from all strings

    full_name: str = Field(min_length=2, max_length=100)                                            # name must be 2-100 characters
    email: EmailStr                                                                                 # must be a valid email format (needs email-validator package)
    password: str                                                                                   # raw password, validated by strong_password below
    confirm_password: str                                                                           # second entry of password to catch typos
    invite_code: str = Field(min_length=1, max_length=200)                                          # secret code that authorizes admin signup

    @field_validator("email")                                                                       # runs only on the email field
    @classmethod                                                                                    # validator receives the class, not an instance
    def lowercase_email(cls, value):                                                                # normalizes email casing
        """
        WHY WE USE THIS FUNCTION:
        - Emails are case-insensitive in practice (Admin@x.com == admin@x.com).
        - Lowercasing before saving prevents duplicate accounts and
          login failures caused by different capitalization.
        """
        return value.lower()                                                                        # store/compare email in lowercase only

    @field_validator("password")                                                                    # runs only on the password field
    @classmethod                                                                                    # validator receives the class, not an instance
    def strong_password(cls, value):                                                                # enforces the password rules
        """
        WHY WE USE THIS FUNCTION:
        - Plugs the shared validate_password_strength helper into this schema.
        - Ensures new admin accounts never use weak passwords.
        """
        return validate_password_strength(value)                                                    # raises error if weak, else returns password

    @model_validator(mode="after")                                                                  # runs after ALL fields are individually validated
    def passwords_match(self):                                                                      # compares two fields against each other
        """
        WHY WE USE THIS FUNCTION:
        - A field validator only sees one field; comparing password with
          confirm_password needs access to the whole model, so we use a
          model validator.
        - mode="after" means both fields are already validated and available.
        - Prevents accounts created with a mistyped password.
        """
        if self.password != self.confirm_password:                                                  # the two entries differ
            raise ValueError("Passwords do not match")                                              # reject the request
        return self                                                                                 # must return the model itself in "after" mode


class AdminLogin(BaseModel):                                                                        # schema for the login request body
    """
    WHY WE USE THIS CLASS:
    - Validates the login payload (email + password).
    - Does NOT apply strength rules to the password on purpose: login should
      only check credentials, and old accounts may have older password rules.
    """

    model_config = ConfigDict(str_strip_whitespace=True)                                            # trim accidental spaces around inputs

    email: EmailStr                                                                                 # must be a valid email format
    password: str = Field(min_length=1, max_length=200)                                             # not empty; max length stops oversized input abuse

    @field_validator("email")                                                                       # runs only on the email field
    @classmethod                                                                                    # validator receives the class, not an instance
    def lowercase_email(cls, value):                                                                # same normalization as registration
        """
        WHY WE USE THIS FUNCTION:
        - Registration saves emails in lowercase, so login must lowercase too,
          otherwise "Admin@x.com" would fail to find "admin@x.com".
        """
        return value.lower()                                                                        # make the email match what is stored in the DB


class AdminResponse(BaseModel):                                                                     # schema for admin data sent BACK to the client
    """
    WHY WE USE THIS CLASS:
    - Controls exactly which admin fields are exposed in API responses.
    - Leaves out password_hash and other sensitive columns so they never leak.
    """

    id: int                                                                                         # admin's database ID
    full_name: str                                                                                  # admin's display name
    email: str                                                                                      # admin's email address
    role: str                                                                                       # admin's role (e.g. "admin", "superadmin")

    model_config = ConfigDict(from_attributes=True)                                                 # lets pydantic read data from SQLAlchemy ORM objects


class AuthResponse(BaseModel):                                                                      # schema for the response after login/register
    """
    WHY WE USE THIS CLASS:
    - Gives a consistent response shape: a status message plus the admin details.
    - Nesting AdminResponse reuses the safe field list defined above.
    """

    message: str                                                                                    # human-readable text, e.g. "Login successful"
    admin: AdminResponse                                                                            # the admin's safe public data
