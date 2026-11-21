# Streamlit app for the customer segment predictor (app.py).
# pandas 3 / numpy 2.5 need Python 3.11+.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Only the files app.py reads at runtime (see .dockerignore).
COPY app.py validation.py cluster_model.joblib input_schema.json metrics.json \
     sample_batch.csv confusion_matrix.png MODEL_CARD.md ./

RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
