# web/auth.py
import hmac
import os
from itsdangerous import URLSafeSerializer, BadData
from fastapi import Request


def _serializer() -> URLSafeSerializer:
    secret = os.getenv("SECRET_KEY", "dev-secret-change-me")
    return URLSafeSerializer(secret, salt="session")


def make_session_cookie(username: str) -> str:
    return _serializer().dumps({"user": username})


def get_current_user(request: Request) -> str | None:
    token = request.cookies.get("session")
    if not token:
        return None
    try:
        data = _serializer().loads(token)
        if not isinstance(data, dict):
            return None
        return data.get("user")
    except BadData:
        return None


def check_credentials(username: str, password: str) -> bool:
    expected_user = os.getenv("DASHBOARD_USER", "admin")
    expected_pass = os.getenv("DASHBOARD_PASSWORD", "changeme")
    return (
        hmac.compare_digest(username, expected_user)
        and hmac.compare_digest(password, expected_pass)
    )
