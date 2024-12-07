FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Only copy the specific requirements file first
COPY ./req.txt /app/req.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/req.txt

# Copy the rest of the application files
COPY . /app

# Expose the application port
EXPOSE 5000

# Set the command to start the application
CMD ["gunicorn", "--worker-class=gevent", "--workers=5", "--max-requests=200", "--max-requests-jitter=20", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
