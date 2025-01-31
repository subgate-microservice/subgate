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
