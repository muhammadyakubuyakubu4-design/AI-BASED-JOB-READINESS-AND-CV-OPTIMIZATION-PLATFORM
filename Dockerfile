FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    gcc \
    pkg-config \
    libcairo2-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y gcc pkg-config libcairo2-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN python -m spacy download en_core_web_sm

COPY . .

RUN python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')" 2>/dev/null || true

RUN python manage.py collectstatic --noinput --clear 2>/dev/null || true

EXPOSE 8000

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
