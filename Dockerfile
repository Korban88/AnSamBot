FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей отдельным слоем
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только нужные файлы
COPY main.py config.py ./

CMD ["python", "main.py"]
