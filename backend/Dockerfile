FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OCR and image processing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    # OCR dependencies
    tesseract-ocr \
    tesseract-ocr-eng \
    # Image processing libraries
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libwebp-dev \
    # PDF processing dependencies
    poppler-utils \
    ghostscript \
    # XML/XSLT support
    libxml2-dev \
    libxslt-dev \
    # Additional system libraries
    pkg-config \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create necessary directories with proper permissions
RUN mkdir -p /app/src/uploads /app/src/temp \
    && useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check removed per user request

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
