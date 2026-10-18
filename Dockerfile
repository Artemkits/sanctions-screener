FROM python:3.12-slim

# Hugging Face Spaces runs containers as uid 1000
RUN useradd -m -u 1000 app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
RUN mkdir -p /app/data && chown app:app /app/data
USER app

ENV DATA_DIR=/app/data PORT=7860 PYTHONUNBUFFERED=1 AUTO_REFRESH_HOURS=24
# Lists are downloaded at build time so the first request is fast;
# start.sh refreshes them when the container restarts and the data is stale.
RUN python -m app.update || true
# build the search index once at image build time so the container starts in seconds
RUN python -c "from app.matcher import get_index; get_index()" || true
EXPOSE 7860
CMD ["./start.sh"]
