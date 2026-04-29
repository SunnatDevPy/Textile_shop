import os
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BaseConfig:
    def asdict(self):
        return asdict(self)


@dataclass
class DatabaseConfig(BaseConfig):
    """Database connection variables"""
    NAME: str = os.getenv('DB_NAME')
    USER: str = os.getenv('DB_USER')
    PASS: str = os.getenv('DB_PASS')
    HOST: str = os.getenv('DB_HOST')
    PORT: str = os.getenv('DB_PORT')

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.NAME}"

@dataclass
class Configuration:
    """All in one configuration's class"""
    db = DatabaseConfig()
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ADMIN_PASS: str = os.getenv('ADMIN_PASS')
    ADMIN_USERNAME: str = os.getenv('ADMIN_USERNAME')
    CLICK_SECRET_KEY: str = os.getenv('CLICK_SECRET_KEY', '')
    PAYME_SECRET_KEY: str = os.getenv('PAYME_SECRET_KEY', '')
    PAYMENT_CALLBACK_IP_WHITELIST: str = os.getenv('PAYMENT_CALLBACK_IP_WHITELIST', '')
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv('RATE_LIMIT_PER_MINUTE', '120'))
    SMTP_ENABLED: bool = os.getenv('SMTP_ENABLED', 'false').lower() in {'1', 'true', 'yes', 'on'}
    SMTP_HOST: str = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '465'))
    SMTP_USER: str = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL: str = os.getenv('SMTP_FROM_EMAIL', os.getenv('SMTP_USER', ''))
    TG_BOT_TOKEN: str = os.getenv('TG_BOT_TOKEN', '')
    TG_GROUP_IDS: str = os.getenv('TG_GROUP_IDS', '')
    TG_WEBHOOK_SECRET: str = os.getenv('TG_WEBHOOK_SECRET', '')
    TG_WEBHOOK_URL: str = os.getenv('TG_WEBHOOK_URL', '')

# class CustomFileSystemStorage(FileSystemStorage):
#
#     def __init__(self, path: str) -> None:
#         self.MEDIA_URL = 'media'
#         self._path = path
#         Path(self.MEDIA_URL).mkdir(parents=True, exist_ok=True)
#
#     def get_path(self, name: str) -> str:
#         return str(self._path / Path(name))
#


def get_currency_in_sum() -> tuple[Optional[int], bool]:
    url = "https://cbu.uz/oz/arkhiv-kursov-valyut/json/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for currency in data:
            if currency['Ccy'] == 'USD':
                return int(float(currency['Rate'])), True
    return None, False


conf = Configuration()
# storage = CustomFileSystemStorage
