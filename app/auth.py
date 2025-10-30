from __future__ import annotations

import hashlib
import hmac
from typing import Final

from fastapi import HTTPException, Request, Response, status

import config

AUTH_COOKIE_NAME: Final = "admin_auth"


def verify_credentials(username: str, password: str) -> bool:
    """Validate administrator credentials."""

    return username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD


def _sign_username(username: str) -> str:
    secret = config.SESSION_SECRET_KEY.encode("utf-8")
    message = username.encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def login_user(response: Response) -> None:
    """Issue an authentication cookie for the administrator."""

    signature = _sign_username(config.ADMIN_USERNAME)
    token = f"{config.ADMIN_USERNAME}:{signature}"
    response.set_cookie(
        AUTH_COOKIE_NAME,
        token,
        httponly=True,
        max_age=60 * 60 * 12,  # 12 hours
        samesite="lax",
    )


def logout_user(response: Response) -> None:
    """Clear the authentication cookie from the client."""

    response.delete_cookie(AUTH_COOKIE_NAME)


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return False

    try:
        username, signature = token.split(":", 1)
    except ValueError:
        return False

    if username != config.ADMIN_USERNAME:
        return False

    expected_signature = _sign_username(username)
    return hmac.compare_digest(signature, expected_signature)


def require_login(request: Request) -> None:
    """Dependency that ensures the user is authenticated."""

    if not _is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Authentication required",
            headers={"Location": "/admin/login"},
        )

