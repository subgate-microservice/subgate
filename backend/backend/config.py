DB_NAME = "subscription_db"
DB_USER = "barma"
DB_PASSWORD = "145190hfp"
DB_HOST = "localhost"
DB_PORT = 27017

HOST = "0.0.0.0"
PORT = 3000

ENCRYPTOR_PASS = "HelloWorld"

FIEF_BASE_URL = "http://localhost:8000"
FIEF_CLIENT_ID = "qsscgXfp53_0LkJoBgzSDRt1TtpkzOWGuWFErBf_dtA"
FIEF_CLIENT_SECRET = "UaEu1Km60IiUODGnxKun-d9RjvKW2KMU3See7f-j3YE"
FIEF_ADMIN_APIKEY = "5RrVaAIhtuvkal1L2C4xzTVbmrejHCGYD6ErZFjjBGA"
FIEF_REDIRECT_URLS = {
    "http://localhost:5173/auth/callback",
    "http://localhost:5000/auth/callback",
    "http://localhost/auth/callback",
}
FIEF_EVENTS = {"user.deleted"}
FIEF_WEBHOOK_BASE_URL = "http://localhost:3000/fief-router"

POSTGRES_URL = f"postgresql+asyncpg://postgres:145190hfp@localhost:5432/subtrack"
