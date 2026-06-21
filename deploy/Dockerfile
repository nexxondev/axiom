FROM python:3.12-slim

LABEL maintainer="Nexxon National <dev@nexxonnational.com>"
LABEL description="AXIOM — Adaptive eXecution Intelligence for Operations Management"
LABEL classification="UNCLASSIFIED"
LABEL version="0.1.0"

WORKDIR /app

# Security: non-root user
RUN groupadd -r axiom && useradd -r -g axiom axiom

# Dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic pydantic-settings \
    sqlalchemy asyncpg alembic python-jose[cryptography] passlib[bcrypt] \
    python-multipart httpx shapely langgraph langchain langchain-openai \
    structlog python-dotenv cryptography aiofiles

# Application
COPY app/ ./app/
COPY frontend/ ./frontend/

# Permissions
RUN chown -R axiom:axiom /app
USER axiom

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import httpx; r=httpx.get('http://localhost:8000/api/v1/health'); exit(0 if r.status_code==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
