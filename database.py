import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL
import logging

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """PostgreSQL veritabanına bağlantı oluşturur"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Veritabanı bağlantısı hatası: {str(e)}")
        raise

def insert_user(firebase_uid, email=None, display_name=None):
    """Yeni bir kullanıcıyı veritabanına ekler
    
    Args:
        firebase_uid (str): Firebase kullanıcı ID'si
        email (str, optional): Kullanıcı e-posta adresi
        display_name (str, optional): Kullanıcı görünen adı
        
    Returns:
        dict: Eklenen kullanıcı bilgileri
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Firebase UID'nin veritabanında olup olmadığını kontrol et
            cur.execute("SELECT * FROM users WHERE firebase_uid = %s", (firebase_uid,))
            existing_user = cur.fetchone()
            
            if existing_user:
                logger.info(f"Kullanıcı zaten mevcut: {firebase_uid}")
                return dict(existing_user)
            
            # Yeni kullanıcı ekle
            cur.execute(
                """
                INSERT INTO users (firebase_uid, email, display_name, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id, firebase_uid, email, display_name, created_at
                """,
                (firebase_uid, email, display_name)
            )
            new_user = cur.fetchone()
            logger.info(f"Yeni kullanıcı eklendi: {firebase_uid}")
            return dict(new_user)
    except Exception as e:
        logger.error(f"Kullanıcı ekleme hatası: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def update_user(firebase_uid, email=None, display_name=None):
    """Kullanıcı bilgilerini günceller
    
    Args:
        firebase_uid (str): Firebase kullanıcı ID'si
        email (str, optional): Yeni e-posta adresi
        display_name (str, optional): Yeni görünen ad
        
    Returns:
        dict: Güncellenen kullanıcı bilgileri
    """
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Kullanıcıyı güncelle
            cur.execute(
                """
                UPDATE users
                SET email = COALESCE(%s, email), 
                    display_name = COALESCE(%s, display_name),
                    updated_at = CURRENT_TIMESTAMP
                WHERE firebase_uid = %s
                RETURNING id, firebase_uid, email, display_name, updated_at
                """,
                (email, display_name, firebase_uid)
            )
            updated_user = cur.fetchone()
            
            if updated_user:
                logger.info(f"Kullanıcı güncellendi: {firebase_uid}")
                return dict(updated_user)
            else:
                logger.warning(f"Güncellenecek kullanıcı bulunamadı: {firebase_uid}")
                return None
    except Exception as e:
        logger.error(f"Kullanıcı güncelleme hatası: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def delete_user(firebase_uid):
    """Kullanıcıyı veritabanından siler
    
    Args:
        firebase_uid (str): Firebase kullanıcı ID'si
        
    Returns:
        bool: İşlem başarılı ise True
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE firebase_uid = %s", (firebase_uid,))
            if cur.rowcount > 0:
                logger.info(f"Kullanıcı silindi: {firebase_uid}")
                return True
            else:
                logger.warning(f"Silinecek kullanıcı bulunamadı: {firebase_uid}")
                return False
    except Exception as e:
        logger.error(f"Kullanıcı silme hatası: {str(e)}")
        raise
    finally:
        if conn:
            conn.close() 