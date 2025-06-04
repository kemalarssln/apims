import firebase_admin
from firebase_admin import credentials, auth
import os
import json
import logging
from config import FIREBASE_CREDENTIALS_PATH
from database import insert_user, update_user, delete_user

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FirebaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Firebase Admin SDK'yi başlatır"""
        try:
            # Credentials dosyasının varlığını kontrol et
            if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
                raise FileNotFoundError(f"Firebase credentials dosyası bulunamadı: {FIREBASE_CREDENTIALS_PATH}")
            
            # Firebase Admin SDK'yi başlat
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            self.app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK başarıyla başlatıldı")
        except Exception as e:
            logger.error(f"Firebase başlatma hatası: {str(e)}")
            raise
    
    def verify_id_token(self, id_token):
        """Firebase ID token'ı doğrular
        
        Args:
            id_token (str): Firebase ID token
            
        Returns:
            dict: Doğrulanmış token bilgileri
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Token doğrulama hatası: {str(e)}")
            raise
    
    def create_user(self, email, password, display_name=None):
        """Firebase'de yeni kullanıcı oluşturur ve PostgreSQL'e kaydeder
        
        Args:
            email (str): Kullanıcı e-posta adresi
            password (str): Kullanıcı şifresi
            display_name (str, optional): Kullanıcı görünen adı
            
        Returns:
            dict: Oluşturulan kullanıcı bilgileri
        """
        try:
            # Firebase'de kullanıcı oluştur
            user = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            # PostgreSQL'e kullanıcıyı kaydet
            db_user = insert_user(
                firebase_uid=user.uid,
                email=email,
                display_name=display_name
            )
            
            logger.info(f"Kullanıcı başarıyla oluşturuldu: {user.uid}")
            return {
                "firebase_user": {
                    "uid": user.uid,
                    "email": user.email,
                    "display_name": user.display_name
                },
                "db_user": db_user
            }
        except Exception as e:
            logger.error(f"Kullanıcı oluşturma hatası: {str(e)}")
            raise
    
    def update_user_info(self, uid, email=None, display_name=None):
        """Firebase ve PostgreSQL'de kullanıcı bilgilerini günceller
        
        Args:
            uid (str): Firebase kullanıcı ID'si
            email (str, optional): Yeni e-posta adresi
            display_name (str, optional): Yeni görünen ad
            
        Returns:
            dict: Güncellenen kullanıcı bilgileri
        """
        try:
            # Güncelleme parametrelerini oluştur
            update_params = {}
            if email is not None:
                update_params['email'] = email
            if display_name is not None:
                update_params['display_name'] = display_name
            
            # Firebase'de kullanıcıyı güncelle
            if update_params:
                user = auth.update_user(uid, **update_params)
                
                # PostgreSQL'de kullanıcıyı güncelle
                db_user = update_user(
                    firebase_uid=uid,
                    email=email,
                    display_name=display_name
                )
                
                logger.info(f"Kullanıcı başarıyla güncellendi: {uid}")
                return {
                    "firebase_user": {
                        "uid": user.uid,
                        "email": user.email,
                        "display_name": user.display_name
                    },
                    "db_user": db_user
                }
            else:
                logger.warning("Güncelleme için parametre belirtilmedi")
                return None
        except Exception as e:
            logger.error(f"Kullanıcı güncelleme hatası: {str(e)}")
            raise
    
    def delete_user_account(self, uid):
        """Firebase ve PostgreSQL'den kullanıcıyı siler
        
        Args:
            uid (str): Firebase kullanıcı ID'si
            
        Returns:
            bool: İşlem başarılı ise True
        """
        try:
            # Firebase'den kullanıcıyı sil
            auth.delete_user(uid)
            
            # PostgreSQL'den kullanıcıyı sil
            db_result = delete_user(uid)
            
            logger.info(f"Kullanıcı başarıyla silindi: {uid}")
            return True
        except Exception as e:
            logger.error(f"Kullanıcı silme hatası: {str(e)}")
            raise
    
    def get_user_by_email(self, email):
        """E-posta adresine göre kullanıcı bilgilerini getirir
        
        Args:
            email (str): Kullanıcı e-posta adresi
            
        Returns:
            dict: Kullanıcı bilgileri
        """
        try:
            user = auth.get_user_by_email(email)
            return {
                "uid": user.uid,
                "email": user.email,
                "display_name": user.display_name,
                "phone_number": user.phone_number,
                "photo_url": user.photo_url,
                "disabled": user.disabled
            }
        except auth.UserNotFoundError:
            logger.warning(f"Kullanıcı bulunamadı: {email}")
            return None
        except Exception as e:
            logger.error(f"Kullanıcı getirme hatası: {str(e)}")
            raise
    
    def handle_auth_event(self, event_type, user_data):
        """Firebase Auth olaylarını işler ve PostgreSQL'e yansıtır
        
        Args:
            event_type (str): Olay tipi (create, update, delete)
            user_data (dict): Kullanıcı verileri
            
        Returns:
            dict: İşlem sonucu
        """
        try:
            if event_type == "create":
                # Yeni kullanıcı oluşturuldu
                db_user = insert_user(
                    firebase_uid=user_data.get("uid"),
                    email=user_data.get("email"),
                    display_name=user_data.get("display_name")
                )
                return {"status": "success", "message": "Kullanıcı eklendi", "user": db_user}
            
            elif event_type == "update":
                # Kullanıcı güncellendi
                db_user = update_user(
                    firebase_uid=user_data.get("uid"),
                    email=user_data.get("email"),
                    display_name=user_data.get("display_name")
                )
                return {"status": "success", "message": "Kullanıcı güncellendi", "user": db_user}
            
            elif event_type == "delete":
                # Kullanıcı silindi
                success = delete_user(user_data.get("uid"))
                return {"status": "success", "message": "Kullanıcı silindi", "result": success}
            
            else:
                logger.warning(f"Bilinmeyen olay tipi: {event_type}")
                return {"status": "error", "message": "Bilinmeyen olay tipi"}
        
        except Exception as e:
            logger.error(f"Auth olay işleme hatası: {str(e)}")
            return {"status": "error", "message": str(e)} 