# Dockerfile — fixed Python 3.11 environment
FROM python:3.11-slim

# set workdir
WORKDIR /app

# copy only requirements first (better caching)
COPY requirements.txt /app/

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy rest of the project
COPY . /app

# create a non-root user (optional but good)
RUN useradd -m appuser || true
USER appuser

# expose port (Render uses $PORT, default fallback 10000)
EXPOSE 10000

# start command — use PORT env if provided
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
