FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "cforge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
