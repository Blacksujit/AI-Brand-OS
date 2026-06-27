FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml .
RUN pip install --user -e "."

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN groupadd -r brandos && useradd -r -g brandos brandos

COPY --from=builder /root/.local /home/brandos/.local
COPY . .

RUN mkdir -p /app/data /app/knowledge && chown -R brandos:brandos /app/data /app/knowledge

ENV PATH=/home/brandos/.local/bin:$PATH \
    HOME=/home/brandos

USER brandos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
