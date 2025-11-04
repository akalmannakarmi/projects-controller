from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.api.deps import get_db
from app.db.models import User, RefreshToken
from app.schemas.user import AccessTokenResponse, RefreshRequest, UserLogin, Token
from app.core.security import verify_password, create_token, decode_token

router = APIRouter()


@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # Find user by email
    user = db.execute(
        select(User).where(User.email == user_in.email)
    ).scalar_one_or_none()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    refresh_token = create_token({"userId": user.id, "type": "refresh"}, "refresh")
    access_token = create_token({"userId": user.id, "type": "access"})

    db.add(RefreshToken(token=refresh_token, user_id=user.id))
    db.commit()

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
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
    stored_token = db.execute(
        select(RefreshToken).where(RefreshToken.token == data.refresh_token)
    ).scalar_one_or_none()
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not found"
        )

    user_id = payload.get("data", {}).get("userId")
    new_access_token = create_token({"userId": user_id, "type": "access"})

    return {"access_token": new_access_token}


@router.post("/logout")
def logout(data: RefreshRequest, db: Session = Depends(get_db)):
    """Delete the refresh token from DB."""
    db.execute(delete(RefreshToken).where(RefreshToken.token == data.refresh_token))
    db.commit()
    return {"message": "Logged out successfully"}
