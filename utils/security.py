import os

from datetime import datetime, timedelta, timezone
from pprint import pprint
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from jose import JWTError, jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext

from database import database
from models.responses import TokenData
from models.responses import LearnerInDB, StaffInDB

from jose.exceptions import ExpiredSignatureError


from pydantic import ValidationError

from dotenv import load_dotenv

load_dotenv()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", scopes={"me": "Read information about the current user.", "get-l-s": "Get users of type learner or staff", "add-u": "Add user", "update-u": "Update a user", "add-u-i": "Add user image", "get-u-i": "Get user image", "get-u": "Get user", "delete-u": "Delete user", "add-d": "Add duty", "assign-s-d": "Assign special duties", "assign-d": "Assigned duties", "get-a-d": "Get assigned duties", "get-d": "Get duties", "update-d": "Update duty", "view-a-d": "View assigned duty", "delete-d": "Delete duty", "mark": "Mark assigned duty"})


def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''Verifies that `plain_password` and `hashed_password` are equal'''
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    '''Returns a hash of the `password`'''
    return pwd_context.hash(password)

async def get_user(username: str):
    
    user_in_db = await database.users.find_one({"_id": username})
    
    if user_in_db:
        
        if user_in_db.get("type") == "learner":
            user_in_db = LearnerInDB(**user_in_db).model_dump()
            user_in_db.update({
                "type": user_in_db.get("type").value,
                "block": user_in_db.get("block").value
            })
            
            return user_in_db
            
        elif user_in_db.get("type") == "staff":
            user_in_db = StaffInDB(**user_in_db).model_dump()
            user_in_db.update({
                "type": user_in_db.get("type").value,
                "role": user_in_db.get("role").value
            })
            
            return user_in_db
        
    return user_in_db


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    
    if not user:
        return False
    if not verify_password(password, user.get("password")):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    
    return encoded_jwt


async def get_current_user(security_scopes: SecurityScopes, token: Annotated[str, Depends(oauth2_scheme)]):
    
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=os.getenv("ALGORITHM"))
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes")
        token_data = TokenData(scopes=token_scopes, username=username)
    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your token has expired"
        )
    user = await get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def get_current_active_user(current_user: Annotated[dict, Security(get_current_user, scopes=["me"])]):
    if not current_user.get("active"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is inactive")
    return current_user