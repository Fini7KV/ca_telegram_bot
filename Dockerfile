# Dockerfile — fixed Python 3.11 environment 
FROM python:3.11-slim

WORKDIR /app

# copy requirements first
COPY requirements.txt /app/

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy rest of the project
COPY . /app

# create a non-root user
RUN useradd -m appuser || true
USER appuser

# expose port
EXPOSE 10000

# start command (Render will pass $PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
