import logging
from typing import Literal

from pydantic import BaseModel, PostgresDsn, AmqpDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

LOG_DEFAULT_FORMAT = (
    "[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
)


WORKER_LOG_DEFAULT_FORMAT = "[%(asctime)s.%(msecs)03d][%(processName)s] %(module)16s:%(lineno)-3d %(levelname)-7s - %(message)s"


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class GunicornConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    timeout: int = 900


class LoggingConfig(BaseModel):
    log_level: Literal[
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    ] = "info"
    log_format: str = LOG_DEFAULT_FORMAT
    date_format: str = "%Y-%m-%d %H:%M:%S"

    @property
    def log_level_value(self) -> int:
        return logging.getLevelNamesMapping()[self.log_level.upper()]


class ApiV1Prefix(BaseModel):
    prefix: str = "/v1"


class ApiPrefix(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    gunicorn: GunicornConfig = GunicornConfig()
    logging: LoggingConfig = LoggingConfig()
    api: ApiPrefix = ApiPrefix()

    db: DatabaseConfig

    rabbitmq_url: AmqpDsn = "amqp://guest:guest@rabbitmq:5672//"

    # API Key
    api_key: str = "secret-api-key"

    PROJECT_NAME: str = "Payment Processing Service"
    # Outbox
    OUTBOX_PUBLISH_INTERVAL: int = 5  # секунды между публикациями
    rmq_payments_queue: str = "payments.new"

    # Webhook retry
    WEBHOOK_MAX_RETRIES: int = 3
    WEBHOOK_RETRY_BASE_DELAY: float = 1.0  # секунд, экспонента

    # Payment simulation
    PAYMENT_PROCESS_MIN_SECONDS: float = 2.0
    PAYMENT_PROCESS_MAX_SECONDS: float = 5.0
    PAYMENT_SUCCESS_RATE: float = 0.9


settings = Settings()
