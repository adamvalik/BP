FROM python:3.11

ENV PYTHONUNBUFFERED=1

# uncomment to support multi-format
# RUN apt-get update && apt-get install -y \
#     libgl1 \
#     libglib2.0-0 \
#     tesseract-ocr \
#     poppler-utils \
#     && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# uncomment to support multi-format
# COPY requirements_multiformat.txt .
# RUN pip install --no-cache-dir -r requirements_multiformat.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
