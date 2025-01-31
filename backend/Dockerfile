# Указываем имя образа
#LABEL name="subtrack-backend"

# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml poetry.lock /app/
RUN poetry install --no-root --no-dev
COPY backend /app/backend/

EXPOSE 3000

# Устанавливаем точку входа
CMD ["poetry", "run", "python", "-m", "backend.main"]
