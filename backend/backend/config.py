import os

from dotenv import load_dotenv

load_dotenv()

# Настройки базы данных
DB_NAME = os.getenv("DB_NAME", "subgate")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "qwerty")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))

# Server settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 3000))

# First user
USER_EMAIL = os.getenv("USER_EMAIL", "test@test.com")
USER_PASSWORD = os.getenv("USER_PASSWORD", "qwerty")
USER_APIKEY_TITLE = os.getenv("USER_APIKEY_TITLE", "Test apikey")
USER_APIKEY_PUBLIC_ID = os.getenv("USER_APIKEY_PUBLIC_ID", "apikey_test_id")
USER_APIKEY_SECRET = os.getenv("USER_APIKEY_SECRET", "test_secret")

# Authentication settings
AUTHENTICATION_CACHE_TIME = int(os.getenv("AUTHENTICATION_CACHE_TIME", 3600))
AUTHENTICATION_TOKEN_LIFETIME = int(os.getenv("AUTHENTICATION_TOKEN_LIFETIME", 86_400))
SECRET = os.getenv("SECRET", "sample_secret")

# Subscription manager
SUBSCRIPTION_MANAGER_CHECK_PERIOD = int(os.getenv("SUBSCRIPTION_MANAGER_CHECK_PERIOD", 3600))
SUBSCRIPTION_MANAGER_BULK_LIMIT = int(os.getenv("SUBSCRIPTION_MANAGER_BULK_LIMIT", 100))

# Cleaners
LOG_RETENTION_DAYS = int(os.getenv("LOG_RETENTION_DAYS", 7))
DELIVERY_RETENTION_DAYS = int(os.getenv("DELIVERY_RETENTION_DAYS", 7))
