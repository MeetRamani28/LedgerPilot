from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import jwt
from jwt import PyJWKClient
from app.core.config import settings

security = HTTPBearer(auto_error=False)


class ClerkUser(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    email: Optional[str] = None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> ClerkUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Test / Dev token bypass for deterministic unit tests and offline development
    if token.startswith("test_token_"):
        extracted_user_id = token.removeprefix("test_token_")
        return ClerkUser(user_id=extracted_user_id or "user_default_test")

    # If Clerk is configured with JWKS, verify token against Clerk public keys
    if settings.CLERK_JWKS_URL:
        try:
            jwks_client = PyJWKClient(settings.CLERK_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True},
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token: missing subject")
            return ClerkUser(
                user_id=user_id,
                session_id=payload.get("sid"),
                email=payload.get("email"),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # In development mode without JWKS URL configured, inspect token payload safely
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        user_id = unverified_payload.get("sub", "user_dev_default")
        return ClerkUser(
            user_id=user_id,
            session_id=unverified_payload.get("sid"),
            email=unverified_payload.get("email"),
        )
    except Exception:
        # Fallback if raw token is passed as user identifier
        return ClerkUser(user_id=token)
