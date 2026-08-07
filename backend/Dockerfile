FROM python:3.11-slim

WORKDIR /app

# Install runtime deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code (engine + API + data).
COPY app ./app

EXPOSE 8000

# The engine is stdlib-only; these deps power the API + optional LLM layer.
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
