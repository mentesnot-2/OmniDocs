FROM node:20-bookworm

WORKDIR /app

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

RUN apt-get update && \
    apt-get install --no-install-recommends -y python3 python3-pip python3-venv && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN python3 -m venv /opt/venv && \
    pip install --no-cache-dir -r requirements.txt

RUN cd frontend && \
    npm ci && \
    npm run build

EXPOSE 8000 3000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
