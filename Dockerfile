# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["gunicorn", "--workers=5", "--max-requests=200", "--max-requests-jitter=20", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
