# qisi_ai_kejian API — SQLite-friendly image for Tencent Cloud (CVM / Lighthouse / TCR)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    QISI_DATA_DIR=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY run.sh ./run.sh
RUN chmod +x run.sh && mkdir -p /data

# Persist SQLite outside the container layer
ENV DATABASE_PATH=/data/qisi.db

EXPOSE 8000

# Placeholders — inject real secrets via CVM env / TKE secrets, never bake into image
# WECHAT_APP_ID WECHAT_APP_SECRET WECHAT_PAY_MCH_ID WECHAT_PAY_API_V3_KEY
# WECHAT_PAY_NOTIFY_URL ADMIN_USERNAME ADMIN_PASSWORD

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
