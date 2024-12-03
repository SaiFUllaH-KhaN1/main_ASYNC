FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip==23.2.1 && \
    pip install -r requirements.txt

COPY . .

# Inform Docker about the port the app listens on
EXPOSE 5000

# Start the app using Gunicorn
CMD ["gunicorn", "--worker-class=gevent", "--workers=2", "--worker-connections=1000", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
