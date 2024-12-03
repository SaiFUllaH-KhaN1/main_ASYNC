FROM python:3.9-slim

WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip==23.2.1 && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy application files
COPY . .

# Inform Docker about the port the app listens on
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production

# Start the app using Gunicorn
CMD ["gunicorn", "--worker-class=gevent", "--workers=2", "--worker-connections=1000", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
