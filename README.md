# Firebase Auth PostgreSQL Entegrasyon Servisi

Bu mikroservis, Firebase Authentication ile PostgreSQL veritabanı arasında veri senkronizasyonu sağlar. Kullanıcılar Firebase'de kayıt olduğunda, güncellendiğinde veya silindiğinde, bu değişiklikleri PostgreSQL'deki kullanıcı tablosuna yansıtır.

## Özellikler

- Firebase Authentication olaylarını (kullanıcı kaydı, güncelleme, silme) dinler
- Kullanıcı verilerini PostgreSQL veritabanına kaydeder
- RESTful API ile manuel kullanıcı yönetimi sağlar
- Token tabanlı kimlik doğrulama ile güvenli erişim
- Detaylı loglama ve hata yönetimi

## Render.com Üzerinde Deploy Etme

1. Render.com hesabınıza giriş yapın

2. "New +" düğmesine tıklayın ve "Blueprint" seçeneğini seçin

3. GitHub'dan repo'nuzu bağlayın

4. `render.yaml` dosyasının bulunduğu klasörü seçin

5. Render otomatik olarak yapılandırmayı algılayacak ve servisi oluşturacaktır

6. Ortam değişkenlerini ayarlayın:
   - Render Dashboard'da servisinizi seçin
   - Environment bölümüne gidin
   - Aşağıdaki ortam değişkenlerini ekleyin:
     - `DATABASE_URL`: PostgreSQL bağlantı URL'niz (`postgresql://kullanici:sifre@sunucu:5432/veritabani`)
     - `WEBHOOK_SECRET`: Webhook güvenlik anahtarınız (güçlü bir şifre oluşturun)

7. Firebase kimlik bilgileri dosyasını yükleyin:
   - Render Dashboard'da "Files" bölümüne gidin
   - `firebase-credentials.json` dosyasını yükleyin

8. Servis otomatik olarak başlayacaktır, "Open App" düğmesine tıklayarak erişebilirsiniz

## API Kullanımı

### Kullanıcı Oluşturma

```
POST /users
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password",
  "display_name": "Örnek Kullanıcı"
}
```

### Kullanıcı Güncelleme

```
PUT /users/{firebase_uid}
Authorization: Bearer {id_token}
Content-Type: application/json

{
  "display_name": "Yeni Kullanıcı Adı"
}
```

### Kullanıcı Silme

```
DELETE /users/{firebase_uid}
Authorization: Bearer {id_token}
```

## Firebase Auth Webhook Entegrasyonu

Bu servisi Firebase Authentication ile entegre etmek için Firebase Cloud Functions kullanmalısınız. 

`scripts/setup_firebase_auth_hooks.js` dosyasını Firebase projenizdeki functions klasörüne kopyalayın ve şu değişiklikleri yapın:

```javascript
// Render servis URL'nizi burada belirtin
const SERVICE_URL = 'https://firebase-auth-service.onrender.com';
// Güvenli bir webhook anahtarı tanımlayın (Render'da ayarladığınız ile aynı olmalı)
const WEBHOOK_SECRET = 'sizin-gizli-webhook-anahtariniz';
```

Sonra Firebase Functions'ı deploy edin:

```bash
firebase deploy --only functions
```

## Sorun Giderme

Render dashboard'unda logları kontrol edebilirsiniz:

1. Render Dashboard'da servisinizi seçin
2. Logs bölümüne gidin

## Güvenlik Notları

- Üretim ortamında güçlü bir WEBHOOK_SECRET değeri kullanın
- PostgreSQL bağlantı bilgilerini güvenli bir şekilde saklayın
- CORS ayarlarını ihtiyaca göre düzenleyin
- Firebase credentials dosyasını güvenli bir şekilde yönetin

## License

MIT 