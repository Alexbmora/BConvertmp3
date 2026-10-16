FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Deno: runtime JS que yt-dlp usa para extraer YouTube (EJS).
# Sin él, yt-dlp avisa que la extracción de YouTube está deprecada y faltan formatos.
ENV DENO_INSTALL=/opt/deno
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/opt/deno/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV APP_DOWNLOADS_DIR=/data/downloads
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers"]
