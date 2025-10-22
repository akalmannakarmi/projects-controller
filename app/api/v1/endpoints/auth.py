from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_db
from app.db.models import User, RefreshToken
from app.schemas.user import UserLogin, Token
from app.core.security import verify_password, create_token

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

    db.add(RefreshToken(token=refreshToken))
    await db.commit()

    return {"access_token": accessToken, "refresh_token": refreshToken}
