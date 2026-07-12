from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_token
from app.utils.logger import logger

router = APIRouter()


@router.post("/register")
def register(
    name: str,
    email: str,
    password: str,
    role: str,
    db: Session = Depends(get_db)
):
    logger.info(f"Register attempt | email={email} | role={role}")

    old_user = db.query(User).filter(User.email == email).first()

    if old_user:
        logger.warning(f"Register failed | duplicate email={email}")
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    new_user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role=role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        f"User registered successfully | user_id={new_user.id} "
        f"| email={email} | role={role}"
    )

    return {"message": "User created successfully"}


@router.post("/login")
def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    logger.info(f"Login attempt | email={email}")

    user = db.query(User).filter(User.email == email).first()

    if not user:
        logger.warning(f"Login failed | email={email} | reason=user_not_found")
        raise HTTPException(
            status_code=401,
            detail="Wrong email or password"
        )

    if not verify_password(password, user.password):
        logger.warning(f"Login failed | email={email} | reason=wrong_password")
        raise HTTPException(
            status_code=401,
            detail="Wrong email or password"
        )

    token = create_token({
        "user_id": user.id,
        "role": user.role
    })

    logger.info(
        f"Login success | email={email} "
        f"| user_id={user.id} | role={user.role}"
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }