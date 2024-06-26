# auth.py
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from typing import Annotated
from functools import wraps
from time import time
import inspect

from backend.app.core.exceptions import (
    CredentialsException, 
    PrivilegesException, 
    InexistentUsernameException,
    ExpiredTokenException,
    InactiveUserException,
    MalformedTokenException,
    MissingRequiredClaimException,
)
from backend.app.repositories.users import get_user_repo
from backend.app.models.users import User
from backend.app.database.models.users import UserDB

from backend.app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

JWT_ALGORITHM=settings.JWT_ALGORITHM
JWT_SECRET_KEY=settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=settings.ACCESS_TOKEN_EXPIRE_MINUTES


async def validate_refresh_token(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Validates the refresh token and returns the current user and the token.

    Args:
        token (str): The refresh token to be validated.

    Returns:
        Tuple[User, str]: A tuple containing the current user object and the token.

    Raises:
        ExpiredTokenException: If the token has expired.
        CredentialsException: If the token is invalid or the user credentials are incorrect.
        InactiveUserException: If the user is inactive.
    """
    
    try:
        user_repo = get_user_repo()

        user_has_token, user = user_repo.refresh_token_exists(token)

        if user_has_token:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            username: str = payload.get("sub")
            roles: str = payload.get("roles")
            expiration_date_int = payload.get("exp")

            expiration_date = datetime.fromtimestamp(expiration_date_int)

            if expiration_date < datetime.now():
                raise ExpiredTokenException()

            empty_entry = username is None or roles is None

            if empty_entry or user.user_username != username:
                raise CredentialsException()
        else:
            raise CredentialsException()

    except JWTError:
        raise ExpiredTokenException()

    current_user = user_repo.get_user_by_username(username)

    if current_user is None:
        raise CredentialsException()

    if not current_user.user_is_active:
        raise InactiveUserException(current_user.user_username)

    return current_user, token


# Function to get the user from the database
async def get_user(username: str) -> UserDB | None:
    """
    Retrieve a user from the database by username.

    Args:
        username (str): The username of the user to retrieve.

    Returns:
        UserDB | None: The retrieved user if found, otherwise None.
    """
    user_repository = get_user_repo()
    user = await user_repository.get_user_by_username(username)

    if not user:
        return

    return user


def create_token(
    data: dict, 
    expires_delta: timedelta | None = ACCESS_TOKEN_EXPIRE_MINUTES
):
    """
    Create a JSON Web Token (JWT) with the provided data and expiration time.

    Args:
        data (dict): The data to be encoded in the JWT.
        expires_delta (timedelta | None, optional): The expiration time for the JWT. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        str: The encoded JWT.

    """
    to_encode = data.copy()
    current_time = datetime.now(timezone.utc)

    # Set the expiration time
    expire = current_time + expires_delta

    time_data = {"exp": expire, "iat": datetime.now()}
    to_encode.update(time_data)

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    """
    Retrieves the current user based on the provided token.

    Args:
        token (str): The JWT token used for authentication.

    Returns:
        User: The user object representing the current user.

    Raises:
        ExpiredTokenException: If the token has expired.
        MissingRequiredClaimException: If the 'sub' claim is missing in the token.
        CredentialsException: If the username is missing in the token.
        MalformedTokenException: If the token is malformed.
        InexistentUsernameException: If the username does not exist in the database.
        InactiveUserException: If the user is inactive.
    """
    
    user_repo = get_user_repo()

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload['exp'] <= time():
            raise ExpiredTokenException()
        
        if 'sub' in payload:
            username: str = payload.get("sub")
        else:
            raise MissingRequiredClaimException("sub")
        
        if username is None:
            raise CredentialsException()

    except JWTError:
        raise MalformedTokenException()

    # Get the user from the database
    user = user_repo.get_user_by_username(username=username)

    if user is None:
        raise InexistentUsernameException(username)
    if not user.user_is_active:
        raise InactiveUserException(user.user_username)

    return user


async def is_async(func):
    """
    Checks if a function is asynchronous.

    Args:
        func: The function to check.

    Returns:
        bool: True if the function is asynchronous, False otherwise.
    """
    return (
        inspect.iscoroutinefunction(func)
        or inspect.isasyncgenfunction(func)
        or hasattr(func, "__await__")
    )


# Decorator to check the role
def role_checker(allowed_roles):
    """
    Decorator function that checks if the current user has the required roles to access a view function.
    
    Args:
        allowed_roles (list): A list of roles that are allowed to access the view function.
        
    Returns:
        function: The decorated view function.
    """
    
    def wrapper(func):
        @wraps(func)
        async def decorated_view(
            *args, 
            **kwargs
        ):
            current_user: User = kwargs.get("current_user")
            
            user_roles_set=set(current_user.user_roles)
            allowed_roles_set=set(allowed_roles)

            user_has_permission=user_roles_set.isdisjoint(allowed_roles_set) is False

            if not user_has_permission:
                raise PrivilegesException()

            if await is_async(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
            
        return decorated_view
    
    return wrapper

