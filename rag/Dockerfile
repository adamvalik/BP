FROM python:3.11

ENV PYTHONUNBUFFERED=1

# tools for multi-format support
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements_multiformat.txt .
RUN pip install --no-cache-dir -r requirements_multiformat.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
