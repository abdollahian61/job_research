FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app \
    && mkdir -p /app/data /app/inputs && chown app:app /app/data
COPY --chown=app:app app/ ./app/
COPY --chown=app:app config/ ./config/
COPY --chown=app:app *.py ./
USER 10001:10001
CMD ["python", "worker.py"]
