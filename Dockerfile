FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
ENV OUTBOX_DB=/data/outbox.db
EXPOSE 8000
CMD ["uvicorn", "outbox_lab.api:app", "--host", "0.0.0.0", "--port", "8000"]
