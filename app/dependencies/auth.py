from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SECRET_KEY, ALGORITHM
from app.models.user import User
from app.utils.logger import logger


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        logger.debug(f"Token decoded | user_id={user_id}")

        if user_id is None:
            logger.warning("Token validation failed | reason=user_id_missing")
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError as e:
        logger.warning(f"Token validation failed | reason=invalid_token | error={str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"Token validation failed | user_id={user_id} not found")
        raise HTTPException(status_code=401, detail="User not found")

    logger.info(f"Token validation success | user_id={user.id} | role={user.role}")

    return user