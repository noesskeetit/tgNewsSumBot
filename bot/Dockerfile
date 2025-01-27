FROM python:3.9-slim

# Создадим рабочую директорию
WORKDIR /app

# Скопируем requirements и установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем весь наш код бота
COPY . .

# Запустим бота
CMD ["python", "bot.py"]
