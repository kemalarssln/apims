FROM python:3.9-slim

WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Uygulama portunu aç
EXPOSE 8000

# Uygulamayı çalıştır
CMD ["python", "api.py"] 