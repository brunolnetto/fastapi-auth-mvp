from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm

from backend.app.auth import (
    create_token, 
    authenticate_user, 
    RoleChecker,
)
from backend.app.data import fake_users_db, refresh_tokens
from backend.app.models import User, Token
from backend.app.auth import validate_refresh_token

# Create an instance of the FastAPI class
router=APIRouter()

# Token expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_MINUTES = 120

access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)   

@router.get("/hello")
def hello_func():
    return "Hello World"


@router.get("/data")
def get_data(_: Depends(RoleChecker(allowed_roles=["admin"]))]):
    return {"data": "This is important data"}


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=400, 
            detail="Incorrect username or password"
        )
    
    auth_data={"sub": user.username, "role": user.role}
    access_token = create_token(
        data=auth_data, expires_delta=access_token_expires
    )
    refresh_token = create_token(
        data=auth_data, expires_delta=refresh_token_expires
    )
    
    refresh_tokens.append(refresh_token)
    
    return Token(access_token=access_token, refresh_token=refresh_token)

# Dependency for checking the OAuth2 token

@router.post("/refresh")
async def refresh_access_token(
    token_data: Annotated[tuple[User, str], Depends(validate_refresh_token)]
):
    user, token = token_data
    auth_data={
        "sub": user.username, 
        "role": user.role
    }

    access_token = create_token(
        data=auth_data, expires_delta=access_token_expires
    )
    refresh_token = create_token(
        data=auth_data, expires_delta=refresh_token_expires
    )

    refresh_tokens.remove(token)
    refresh_tokens.append(refresh_token)

    return Token(access_token=access_token, refresh_token=refresh_token)
