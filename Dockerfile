# Imagem de produção do Além do Placar (site + API + assistente).
# Build: docker build -t alem-do-placar .
# Execução: docker run --rm -p 8000:8000 -e LLM_API_KEY=... alem-do-placar

FROM python:3.12-slim AS construtor
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements-web.txt .
RUN pip install -r requirements-web.txt
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ROOT=/app \
    PORT=8000
RUN useradd --system --uid 10001 --home-dir /app app
WORKDIR /app
COPY --from=construtor /opt/venv /opt/venv
# Dados e documentos lidos em tempo de execução (filtrados pelo .dockerignore).
COPY data ./data
COPY docs ./docs
COPY config ./config
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request as u; u.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=4)"
CMD ["python", "-m", "api.main"]
