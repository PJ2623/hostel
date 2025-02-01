import os, json
from datetime import datetime, timedelta, timezone
from pprint import pprint

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes

from jose import JWTError, jwt, jwe
from jwt import InvalidTokenError
from jose.exceptions import ExpiredSignatureError
from . schemas import TokenData


from passlib.context import CryptContext

from pydantic import ValidationError
from typing import Annotated

from models.staff import Staff

from dotenv import load_dotenv

load_dotenv()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", scopes={
    "me": "Read information about the current user.",
    "add-u": "Add user",
    "update-u": "Update a user",
    "get-u-i": "Get user image",
    "get-u": "Get user", 
    "delete-u": "Delete user",
    "add-d": "Add duty",
    "assign-s-d": "Assign special duties",
    "get-a-d": "Get assigned duties", 
    "get-d": "Get duties",
    "update-d": "Update duty",
    "view-a-d": "View assigned duty",
    "delete-d": "Delete duty",
    "get-l-i": "Get learner image",
    "get-l": "Get learner",
    "add-l": "Add learner",
    "mark-d": "Marking duty completion",
    "mark-a": "Mark attendance for an activity",
    "get-a": "Get attendance",
    "delete-l": "Delete a learner"
})


def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''Verifies that `plain_password` and `hashed_password` are equal'''
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    '''Returns a hash of the `password`'''
    return pwd_context.hash(password)

async def get_user(username: str) -> Staff | None:
    
    user_in_db = await Staff.find_one(Staff.id == username)
        
    return user_in_db


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=5)
    to_encode.update({'exp': expire.timestamp()})   #* Add expiration time to payload
    
    to_encode = json.dumps(to_encode).encode('utf-8') #* Convert payload to bytes
    
    #* Create a JWE token
    encoded_jwe = jwe.encrypt(
        to_encode,
        os.getenv("SECRET_KEY"),
        algorithm='dir',
        encryption='A256GCM'
    )
    
    return encoded_jwe


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
        #* Decrypt the JWE token
        token_bytes = token.encode('utf-8')
        payload_bytes = jwe.decrypt(token_bytes, os.getenv("SECRET_KEY"))
        payload: dict = json.loads(payload_bytes)
        
        username = payload.get("sub")
        exp = payload.get("exp")
        token_scopes: list = payload.get("scopes")
        token_data = TokenData(scopes=token_scopes, username=username)
        
        if username is None:
            raise credentials_exception
        
        #* Validate that the token has not expired
        if exp is None or datetime.now(timezone.utc).timestamp() > exp:
            raise ExpiredSignatureError
        
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


async def get_current_active_user(current_user: Annotated[Staff, Security(get_current_user, scopes=["me"])]):
    if not current_user.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is inactive")
    return current_user