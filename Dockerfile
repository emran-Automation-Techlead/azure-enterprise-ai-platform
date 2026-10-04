FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    HOME=/home/app

# Run as a non-root user
RUN useradd --create-home --uid 10001 app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY ui ./ui
COPY evaluation ./evaluation
COPY start.sh .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh && chown -R app:app /app

USER app
EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=4).status==200 else 1)"

CMD ["./start.sh"]
