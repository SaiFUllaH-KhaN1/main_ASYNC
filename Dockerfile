# Use a lighter base image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache layering
COPY requirements.txt .

# Install required packages without cache
RUN pip install --upgrade pip==23.2.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Inform Docker about the port the app listens on
EXPOSE 5000

# Start the app using Gunicorn
CMD ["gunicorn", "--worker-class=gevent", "--workers=2", "--worker-connections=1000", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
