import os
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from dotenv import load_dotenv


def _normalize_env_credential(name: str) -> None:
    """.env / Docker: qo'shtirnoq, bo'shliq, Compose uchun $$ escape."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return
    s = str(raw).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1]
    if name == "ADMIN_PASS" and "$$" in s:
        s = s.replace("$$", "$")
    os.environ[name] = s


load_dotenv()
_normalize_env_credential("ADMIN_USERNAME")
_normalize_env_credential("ADMIN_PASS")


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
    POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '20'))
    MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '30'))
    POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', '60'))
    POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '1800'))

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.USER}:{self.PASS}@{self.HOST}:{self.PORT}/{self.NAME}"

def _payme_relax_amount_units_default() -> bool:
    """Sandbox odatda amount so'm butun soni; prod Payme dokumentatsiyasi bo'yicha tiyn.

    PAYME_RELAX_AMOUNT_UNITS muhiti bo'sh/unset bo'lsa, test checkout hostida moslash (relax),
    aks holda aniq tiyn (strict).
    """
    raw = os.getenv('PAYME_RELAX_AMOUNT_UNITS')
    if raw is not None and str(raw).strip() != '':
        return str(raw).strip().lower() in {'1', 'true', 'yes', 'on'}
    endpoint = os.getenv('PAYME_ENDPOINT', 'https://checkout.paycom.uz').lower()
    return 'test.paycom' in endpoint


def _payme_account_reject_extra_keys_default() -> bool:
    """Sandbox invalid-account testlarida `account` ga qo'shimcha kalit kelishi mumkin.

    PAYME_ACCOUNT_REJECT_EXTRA_KEYS bo'sh bo'lsa, test.paycom uchun faqat ``order_id`` qoldirish.
    """
    raw = os.getenv('PAYME_ACCOUNT_REJECT_EXTRA_KEYS')
    if raw is not None and str(raw).strip() != '':
        return str(raw).strip().lower() in {'1', 'true', 'yes', 'on'}
    endpoint = os.getenv('PAYME_ENDPOINT', 'https://checkout.paycom.uz').lower()
    return 'test.paycom' in endpoint


def _payme_checkperform_busy_default() -> bool:
    """Sandbox: boshqa Payme trx yaratilgan hisob uchun CheckPerform rad (-31088).

    Prod: klientlar CheckPerform ni takrorlay olishi mumkin — odatda o'chiq.
    PAYME_CHECKPERFORM_BUSY_ACCOUNT bo'sh/unset va test.paycom endpoint → yoqiladi.
    """
    raw = os.getenv('PAYME_CHECKPERFORM_BUSY_ACCOUNT')
    if raw is not None and str(raw).strip() != '':
        return str(raw).strip().lower() in {'1', 'true', 'yes', 'on'}
    endpoint = os.getenv('PAYME_ENDPOINT', 'https://checkout.paycom.uz').lower()
    return 'test.paycom' in endpoint


@dataclass
class Configuration:
    """All in one configuration's class"""
    db = DatabaseConfig()
    SECRET_KEY: str = os.getenv('SECRET_KEY')
    ADMIN_PASS: str = os.getenv('ADMIN_PASS')
    ADMIN_USERNAME: str = os.getenv('ADMIN_USERNAME')
    CLICK_SECRET_KEY: str = os.getenv('CLICK_SECRET_KEY', '')
    CLICK_MERCHANT_ID: str = os.getenv('CLICK_MERCHANT_ID', '')
    CLICK_SERVICE_ID: str = os.getenv('CLICK_SERVICE_ID', '')
    CLICK_MERCHANT_USER_ID: str = os.getenv('CLICK_MERCHANT_USER_ID', '')
    PAYME_MERCHANT_ID: str = os.getenv('PAYME_MERCHANT_ID', '')
    PAYME_SECRET_KEY: str = os.getenv('PAYME_SECRET_KEY', '')
    PAYME_ENDPOINT: str = os.getenv('PAYME_ENDPOINT', 'https://checkout.paycom.uz')
    PAYME_RELAX_AMOUNT_UNITS: bool = _payme_relax_amount_units_default()
    PAYME_ACCOUNT_REJECT_EXTRA_KEYS: bool = _payme_account_reject_extra_keys_default()
    PAYME_CHECKPERFORM_BUSY_ACCOUNT: bool = _payme_checkperform_busy_default()
    # Bo'sh — barcha buyurtma id lari Payme uchun ruxsat (prod). Sandbox: "noto'g'ri akkaunt"
    # testlari uchun CSV, masalan "5" (faqat order_id shu ro'yxatda bo'lsa ishlaydi).
    PAYME_ALLOW_ORDER_IDS: str = os.getenv('PAYME_ALLOW_ORDER_IDS', '')
    PUBLIC_BASE_URL: str = os.getenv('PUBLIC_BASE_URL', '')
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
