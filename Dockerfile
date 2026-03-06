# Используем официальный легкий образ Python
FROM python:3.12-slim

# Настройки среды
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN mkdir -p /app/data /app/media

EXPOSE 8000

CMD sh -c "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn MyVolleyApp.wsgi:application --bind 0.0.0.0:8000 --timeout 1000"