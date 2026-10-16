"""
End-to-end API tests for admin auth + protected student CRUD.
Run from the backend folder:   python -m pytest tests -v
Uses a throw-away SQLite file, so your MySQL data is never touched.
"""
import os
import tempfile
from datetime import datetime, timedelta, timezone

_db_file = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-characters-long"
os.environ["ADMIN_INVITE_CODE"] = "letmein-123"

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.auth import rate_limit  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.Model.admin import Admin  # noqa: E402

GOOD = {
    "full_name": "Asha Admin",
    "email": "Asha@Example.com",
    "password": "Str0ngPass",
    "confirm_password": "Str0ngPass",
    "invite_code": "letmein-123",
}


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    rate_limit.clear_all()
    with TestClient(app) as c:
        yield c


def register(client, **overrides):
    return client.post("/admin/register", json={**GOOD, **overrides})


def login(client, email="asha@example.com", password="Str0ngPass"):
    return client.post("/admin/login", json={"email": email, "password": password})


def logged_in(client):
    assert register(client).status_code == 201
    assert login(client).status_code == 200
    return client


# ---------- registration ----------
def test_register_success_and_password_is_hashed(client):
    r = register(client)
    assert r.status_code == 201
    assert r.json()["email"] == "asha@example.com" and r.json()["role"] == "admin"
    assert "password" not in r.text
    with SessionLocal() as db:
        stored = db.query(Admin).one()
        assert stored.hashed_password.startswith("$2") and stored.hashed_password != GOOD["password"]


def test_register_rejects_wrong_invite_code(client):
    assert register(client, invite_code="wrong").status_code == 403


def test_register_blocked_without_invite_code_field(client):
    body = {k: v for k, v in GOOD.items() if k != "invite_code"}
    assert client.post("/admin/register", json=body).status_code == 422


def test_register_duplicate_email_rejected_case_insensitive(client):
    assert register(client).status_code == 201
    assert register(client, email="ASHA@example.COM").status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"password": "short1A", "confirm_password": "short1A"},
        {"password": "alllowercase1", "confirm_password": "alllowercase1"},
        {"password": "NoDigitsHere", "confirm_password": "NoDigitsHere"},
        {"confirm_password": "Different1A"},
        {"email": "not-an-email"},
        {"full_name": "A"},
    ],
)
def test_register_validation(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_invite_code_brute_force_is_throttled(client):
    for _ in range(5):
        assert register(client, invite_code="bad").status_code == 403
    assert register(client, invite_code="bad").status_code == 429


# ---------- login ----------
def test_login_success_sets_httponly_cookie(client):
    register(client)
    r = login(client)
    assert r.status_code == 200 and r.json()["admin"]["email"] == "asha@example.com"
    cookie = r.headers["set-cookie"].lower()
    assert "access_token=" in cookie and "httponly" in cookie and "samesite=lax" in cookie
    assert "access_token" not in r.json()  # token is not exposed to JavaScript


def test_login_invalid_credentials(client):
    register(client)
    assert login(client, password="WrongPass1").status_code == 401
    assert login(client, email="nobody@example.com").status_code == 401


def test_login_lockout_after_repeated_failures(client):
    register(client)
    for _ in range(5):
        assert login(client, password="WrongPass1").status_code == 401
    assert login(client, password="WrongPass1").status_code == 429
    assert login(client).status_code == 429  # even the right password, until the window passes


def test_me_requires_login_and_returns_admin(client):
    assert client.get("/admin/me").status_code == 401
    logged_in(client)
    assert client.get("/admin/me").json()["full_name"] == "Asha Admin"


# ---------- protected students API ----------
@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/students/", None),
        ("get", "/students/1", None),
        ("post", "/students/", {"name": "A", "age": 20, "course": "Math"}),
        ("put", "/students/1", {"name": "A", "age": 20, "course": "Math"}),
        ("delete", "/students/1", None),
    ],
)
def test_students_endpoints_reject_unauthenticated(client, method, path, body):
    r = getattr(client, method)(path, **({"json": body} if body else {}))
    assert r.status_code == 401


def test_student_crud_and_search(client):
    logged_in(client)
    a = client.post("/students/", json={"name": "Meena", "age": 21, "course": "AI"})
    b = client.post("/students/", json={"name": "Ravi", "age": 25, "course": "Data Science"})
    assert a.status_code == 200 and b.status_code == 200
    sid = a.json()["id"]

    assert len(client.get("/students/").json()) == 2
    assert [s["name"] for s in client.get("/students/?search=MEE").json()] == ["Meena"]       # case-insensitive
    assert [s["name"] for s in client.get("/students/?search=data").json()] == ["Ravi"]        # course
    assert [s["name"] for s in client.get("/students/?search=25").json()] == ["Ravi"]          # age
    assert client.get("/students/?search=%25").json() == []                                    # % is literal, not a wildcard

    assert client.put(f"/students/{sid}", json={"name": "Meena K", "age": 22, "course": "AI"}).json()["age"] == 22
    assert client.get(f"/students/{sid}").json()["name"] == "Meena K"

    assert client.delete(f"/students/{sid}").status_code == 200
    assert client.get(f"/students/{sid}").status_code == 404


def test_student_input_validation(client):
    logged_in(client)
    assert client.post("/students/", json={"name": "", "age": 20, "course": "X"}).status_code == 422
    assert client.post("/students/", json={"name": "A", "age": 0, "course": "X"}).status_code == 422
    assert client.post("/students/", json={"name": "A" * 101, "age": 20, "course": "X"}).status_code == 422


# ---------- logout / revocation / expiry ----------
def test_logout_revokes_token_even_if_cookie_is_replayed(client):
    logged_in(client)
    stolen = client.cookies.get("access_token")
    assert client.get("/students/").status_code == 200

    r = client.post("/admin/logout")
    assert r.status_code == 200 and "logged out successfully" in r.json()["message"]
    assert client.get("/students/").status_code == 401
    assert client.get("/admin/me").status_code == 401

    # an attacker replaying the copied token is still rejected (server-side revocation)
    client.cookies.set("access_token", stolen)
    assert client.get("/students/").status_code == 401


def test_logout_without_session_is_harmless(client):
    assert client.post("/admin/logout").status_code == 200


def test_expired_and_tampered_tokens_rejected(client):
    secret = os.environ["SECRET_KEY"]
    now = datetime.now(timezone.utc)
    base = {"sub": "1", "role": "admin", "jti": "abc"}

    expired = jwt.encode({**base, "exp": now - timedelta(minutes=1)}, secret, algorithm="HS256")
    client.cookies.set("access_token", expired)
    r = client.get("/students/")
    assert r.status_code == 401 and "expired" in r.json()["detail"].lower()

    forged = jwt.encode({**base, "exp": now + timedelta(hours=1)}, "some-other-secret-key-0123456789abcdef", algorithm="HS256")
    client.cookies.set("access_token", forged)
    assert client.get("/students/").status_code == 401

    client.cookies.set("access_token", "garbage")
    assert client.get("/students/").status_code == 401


def test_non_admin_role_is_forbidden(client):
    with SessionLocal() as db:
        db.add(Admin(full_name="Stu Dent", email="stu@example.com", hashed_password=hash_password("Str0ngPass"), role="student"))
        db.commit()
    assert login(client, email="stu@example.com").status_code == 403  # cannot even log in

    # and a validly signed token for a non-admin is refused by the API too
    with SessionLocal() as db:
        sid = db.query(Admin).one().id
    token = jwt.encode(
        {"sub": str(sid), "role": "admin", "jti": "x1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        os.environ["SECRET_KEY"], algorithm="HS256",
    )
    client.cookies.set("access_token", token)
    assert client.get("/students/").status_code == 403  # role comes from the DB, not from the token claim


def test_private_responses_are_not_cacheable(client):
    logged_in(client)
    assert client.get("/students/").headers["cache-control"] == "no-store"
    assert client.get("/admin/me").headers["cache-control"] == "no-store"
