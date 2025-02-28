# Используем базовый образ с Node.js
FROM node:18 AS build

# Копируем package.json и package-lock.json для установки зависимостей
COPY package.json package.json
COPY package-lock.json package-lock.json

# Устанавливаем зависимости
RUN npm install

# Копируем весь проект в контейнер
COPY . .

# Собираем фронтенд-приложение с помощью Vite
RUN npm run build

# Используем Nginx для раздачи статических файлов
FROM nginx:stable-alpine

# Копируем собранные файлы в директорию Nginx
COPY --from=build /dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открываем порт для доступа к приложению
EXPOSE 5000

# Запускаем Nginx
CMD ["nginx", "-g", "daemon off;"]
