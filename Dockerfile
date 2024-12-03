# Use a base image that's still light but more compatible than Alpine
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache layering
COPY requirements.txt .

# Update system packages, install dependencies, and clean up in a single layer to keep image size down
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libffi-dev \
    && pip install --upgrade pip==23.2.1 \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove gcc libc6-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of your application code
COPY . .

# Inform Docker about the port the app listens on
EXPOSE 5000

# Start the app using Gunicorn
CMD ["gunicorn", "--worker-class=gevent", "--workers=2", "--worker-connections=1000", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
