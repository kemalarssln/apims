import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Çalışma dizininin kökünü belirle
BASE_DIR = Path(__file__).resolve().parent

# .env dosyası varsa yükle
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Ortam değişkeninden credentials içeriğini al ve dosya olarak kaydet
FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase-credentials.json')

if FIREBASE_CREDENTIALS_JSON and not os.path.exists(FIREBASE_CREDENTIALS_PATH):
    with open(FIREBASE_CREDENTIALS_PATH, 'w') as f:
        f.write(FIREBASE_CREDENTIALS_JSON)

# PostgreSQL bağlantı bilgileri
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Ke485866!@localhost:5432/postgres')

# API Port - Render otomatik olarak PORT çevre değişkeni atar
PORT = int(os.getenv('PORT', 10000))

# Webhook güvenlik anahtarı
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret-key')
