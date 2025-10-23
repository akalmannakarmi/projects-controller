from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.api.deps import get_db
from app.db.models import User, RefreshToken
from app.schemas.user import AccessTokenResponse, RefreshRequest, UserLogin, Token
from app.core.security import verify_password, create_token, decode_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    refreshToken = create_token({"userId": user.id, "type": "refresh"}, "refresh")
    accessToken = create_token({"userId": user.id, "type": "access"})

    db.add(RefreshToken(token=refreshToken, user_id=user.id))
    await db.commit()

    return {"access_token": accessToken, "refresh_token": refreshToken}


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token."""
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("data", {}).get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Validate token exists in DB
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token == data.refresh_token)
    )
    stored_token = result.scalar_one_or_none()
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    userId = payload.get("data", {}).get("userId")
    new_access_token = create_token({"userId": userId, "type": "access"})

    return {"access_token": new_access_token}


@router.post("/logout")
async def logout(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Delete the refresh token from DB."""
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token == data.refresh_token)
    )
    await db.commit()
    return {"message": "Logged out successfully"}
