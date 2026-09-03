FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".[deployment]"

EXPOSE 8000

CMD ["uvicorn", "tigerdatalab.ai.deployment:create_app", "--host", "0.0.0.0", "--port", "8000"]
