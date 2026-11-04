FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app
COPY model_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY scoutiq ./scoutiq
COPY model_service/main.py ./main.py

EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
