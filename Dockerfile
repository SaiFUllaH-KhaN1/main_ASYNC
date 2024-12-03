FROM python:3.10-slim

WORKDIR /app

COPY req.txt .
RUN pip install -r req.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--workers=5", "--max-requests=200", "--max-requests-jitter=20", "--timeout", "550", "routes:app", "--bind", "0.0.0.0:5000"]
