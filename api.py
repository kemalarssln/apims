from fastapi import FastAPI, HTTPException, Depends, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import json
import uvicorn
import traceback
from firebase_service import FirebaseService
from database import insert_user, update_user, delete_user
from config import PORT, WEBHOOK_SECRET

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Firebase Auth PostgreSQL Entegrasyon Servisi",
    description="Firebase Authentication ile PostgreSQL veritabanı entegrasyonu sağlar",
    version="1.0.0"
)

# CORS ayarları - ihtiyaca göre düzenlenebilir
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Güvenlik için üretimde sadece güvenilir domainler eklenmelidir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Firebase servis instance'ı
firebase_service = FirebaseService()

# API Modelleri
class UserCreate(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    display_name: Optional[str] = None

class FirebaseAuthEvent(BaseModel):
    event_type: str = Field(..., description="Olay tipi: create, update, delete")
    user_data: Dict[str, Any] = Field(..., description="Kullanıcı verileri")

# Token doğrulama dependency
async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Geçersiz veya eksik kimlik doğrulama bilgisi")
    
    token = authorization.replace("Bearer ", "")
    try:
        decoded_token = firebase_service.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Token doğrulama hatası: {str(e)}")
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token")

async def verify_webhook_signature(request: Request):
    # İsteğin webhook'tan geldiğini doğrulamak için özel bir imza veya başlık kullanılabilir
    signature = request.headers.get("X-Webhook-Signature")
    if not signature or signature != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook doğrulama başarısız")
    return True

# API Rotaları
@app.get("/")
async def root():
    return {"message": "Firebase Auth PostgreSQL Entegrasyon Servisi", "status": "active"}

@app.get("/health")
async def health_check():
    """Render için sağlık kontrolü endpoint'i"""
    return {"status": "healthy"}

@app.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    try:
        result = firebase_service.create_user(
            email=user_data.email,
            password=user_data.password,
            display_name=user_data.display_name
        )
        return result
    except Exception as e:
        logger.error(f"Kullanıcı oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/users/{uid}", status_code=status.HTTP_200_OK)
async def update_user_info(uid: str, user_data: UserUpdate, token_data: dict = Depends(verify_token)):
    # İsteği yapan kullanıcının yetkisini kontrol et
    if token_data.get("uid") != uid:
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    try:
        result = firebase_service.update_user_info(
            uid=uid,
            email=user_data.email,
            display_name=user_data.display_name
        )
        if result:
            return result
        else:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    except Exception as e:
        logger.error(f"Kullanıcı güncelleme hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/users/{uid}", status_code=status.HTTP_200_OK)
async def delete_user_account(uid: str, token_data: dict = Depends(verify_token)):
    # İsteği yapan kullanıcının yetkisini kontrol et (admin veya kendisi olmalı)
    if token_data.get("uid") != uid and not token_data.get("admin", False):
        raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
    
    try:
        result = firebase_service.delete_user_account(uid)
        return {"status": "success", "message": "Kullanıcı başarıyla silindi"}
    except Exception as e:
        logger.error(f"Kullanıcı silme hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/email/{email}", status_code=status.HTTP_200_OK)
async def get_user_by_email(email: str, token_data: dict = Depends(verify_token)):
    try:
        user = firebase_service.get_user_by_email(email)
        if user:
            return user
        else:
            raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    except Exception as e:
        logger.error(f"Kullanıcı getirme hatası: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Firebase Auth Webhook Endpoint'i
@app.post("/webhook/auth", status_code=status.HTTP_200_OK)
async def firebase_auth_webhook(event: FirebaseAuthEvent, signature_verified: bool = Depends(verify_webhook_signature)):
    try:
        result = firebase_service.handle_auth_event(
            event_type=event.event_type,
            user_data=event.user_data
        )
        return result
    except Exception as e:
        logger.error(f"Webhook işleme hatası: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Hata yakalama
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Genel hata: {str(exc)}")
    traceback.print_exc()
    return Response(
        content=json.dumps({"detail": str(exc)}),
        status_code=500,
        media_type="application/json"
    )

if __name__ == "__main__":
    # API'yi başlat - Render'da bu kod çalışmayacak, gunicorn kullanılacak
    uvicorn.run("api:app", host="0.0.0.0", port=PORT, reload=True) 