from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from pydantic import (
    AnyUrl,
    BeforeValidator,
    computed_field,
    model_validator,
)


from typing import (
    Literal, Union, Annotated, Any, List,
)
from typing_extensions import Self

from warnings import warn
import toml

DEFAULT_PASSWORD = "change_me"
POSTGRES_DSN_SCHEME = "postgresql+psycopg2"


# Project settings
with open("pyproject.toml", "r") as f:
    config = toml.load(f)

def parse_cors(v: Any) -> Union[List[str], str]:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)


# Settings class
class Settings(BaseSettings):
    """App settings."""

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_ignore_empty=True, 
        extra="ignore"
    )

    VERSION: str = config["tool"]["poetry"]["version"]
    PROJECT_NAME: str = config["tool"]["poetry"]["name"]
    DESCRIPTION: str = config["tool"]["poetry"]["description"]
    API_V1_STR: str = "/api"

    COOKIE_SECRET_KEY: str = 'change_me'
    JWT_SECRET_KEY: str = 'change_me'
    JWT_ALGORITHM: str = 'HS256'

    ENVIRONMENT: Literal["development"] = "development"
    DOMAIN: str = "localhost:8000"

    # 1 day
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1 * 24 * 60

    # CORS
    BACKEND_CORS_ORIGINS: Annotated[
        Union[List[AnyUrl], str], BeforeValidator(parse_cors)
    ] = []

    @computed_field
    @property
    def server_host(self) -> str:
        # Use HTTPS for anything other than local development
        protocol = "http" if self.ENVIRONMENT == "development" else "https"
        return f"{protocol}://{self.DOMAIN}"

    # Database settings
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_DBNAME: str = "my_db"

    def database_uri(self) -> str:
        return (
            f"{POSTGRES_DSN_SCHEME}://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DBNAME}"
        )

    def _check_default_secret(self, var_name: str, value: Union[str, None]) -> None:
        if value == DEFAULT_PASSWORD:
            message = (
                f'The value of {var_name} is "{DEFAULT_PASSWORD}", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "development":
                warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)

        return self


settings = Settings()
