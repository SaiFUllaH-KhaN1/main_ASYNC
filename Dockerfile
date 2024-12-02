# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirementsless.txt /app/requirementsless.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirementsless.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--worker-class=gevent", "--worker-connections=1000", "--workers=5", "--timeout", "600", "routes:app", "--bind", "0.0.0.0:5000"]
