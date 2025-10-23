from app.db.session import SessionLocal
from functools import wraps
from fastapi import Request, HTTPException, status
from jose import JWTError
from app.core.security import decode_token


def authenticated(func):
    """
    Decorator that verifies the Authorization Bearer token
    and injects `user_id` into the route kwargs.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Try to get the Request object
        request: Request | None = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if request is None:
            raise RuntimeError("Request object is required as a parameter in the route")

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )

        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            user_id = payload.get("userId")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing userId in token",
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        # Inject user_id into kwargs
        kwargs["user_id"] = user_id
        return await func(*args, **kwargs)

    return wrapper


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()
