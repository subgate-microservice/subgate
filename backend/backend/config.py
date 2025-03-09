import os

from dotenv import load_dotenv

load_dotenv()

# Настройки базы данных
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))

# Настройки сервера
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

# Ключ для шифрования
ENCRYPTOR_PASS = os.getenv("ENCRYPTOR_PASS")

POSTGRES_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# First user
USER_EMAIL = os.getenv("USER_EMAIL", "test@test.com")
USER_PASSWORD = os.getenv("USER_PASSWORD", "qwerty")
USER_APIKEY_TITLE = os.getenv("USER_APIKEY_TITLE", "Test apikey")
USER_APIKEY_PUBLIC_ID = os.getenv("USER_APIKEY_PUBLIC_ID", "apikey_test_id")
USER_APIKEY_SECRET = os.getenv("USER_APIKEY_SECRET", "test_secret")

# Cache settings
AUTHENTICATION_CACHE_TIME = os.getenv("AUTHENTICATION_CACHE_TIME", 3600)

# Subscription manager
SUBSCRIPTION_MANAGER_CHECK_PERIOD = os.getenv("SUBSCRIPTION_MANAGER_CHECK_PERIOD", 10)
SUBSCRIPTION_MANAGER_BULK_LIMIT = os.getenv("SUBSCRIPTION_MANAGER_BULK_LIMIT", 100)


# Cleaners
LOG_RETENTION_DAYS = os.getenv("LOG_RETENTION_DAYS", 7)
DELIVERY_RETENTION_DAYS = os.getenv("DELIVERY_RETENTION_DAYS", 7)
