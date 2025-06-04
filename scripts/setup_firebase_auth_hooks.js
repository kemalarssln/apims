// Firebase Cloud Functions için örnek webhook dosyası
const functions = require('firebase-functions');
const fetch = require('node-fetch');

// Render servis URL'nizi burada belirtin
const SERVICE_URL = 'https://apims.onrender.com';
// Güvenli bir webhook anahtarı - Render'da aynı değeri kullanmalısınız
const WEBHOOK_SECRET = 'sizin-gizli-webhook-anahtariniz';

// Kullanıcı oluşturulduğunda tetiklenir
exports.userCreated = functions.auth.user().onCreate((user) => {
  console.log('Yeni kullanıcı oluşturuldu:', user.uid);
  
  return fetch(`${SERVICE_URL}/webhook/auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': WEBHOOK_SECRET
    },
    body: JSON.stringify({
      event_type: 'create',
      user_data: {
        uid: user.uid,
        email: user.email,
        display_name: user.displayName
      }
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP hata! Durum: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('Kullanıcı veritabanına kaydedildi:', data);
    return data;
  })
  .catch(error => {
    console.error('Webhook çağrısı başarısız:', error);
    throw error;
  });
});

// Kullanıcı güncellendiğinde tetiklenir
exports.userUpdated = functions.auth.user().onUpdate((change) => {
  const before = change.before;
  const after = change.after;
  console.log('Kullanıcı güncellendi:', after.uid);
  
  return fetch(`${SERVICE_URL}/webhook/auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': WEBHOOK_SECRET
    },
    body: JSON.stringify({
      event_type: 'update',
      user_data: {
        uid: after.uid,
        email: after.email,
        display_name: after.displayName
      }
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP hata! Durum: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('Kullanıcı veritabanında güncellendi:', data);
    return data;
  })
  .catch(error => {
    console.error('Webhook çağrısı başarısız:', error);
    throw error;
  });
});

// Kullanıcı silindiğinde tetiklenir
exports.userDeleted = functions.auth.user().onDelete((user) => {
  console.log('Kullanıcı silindi:', user.uid);
  
  return fetch(`${SERVICE_URL}/webhook/auth`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': WEBHOOK_SECRET
    },
    body: JSON.stringify({
      event_type: 'delete',
      user_data: {
        uid: user.uid
      }
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP hata! Durum: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    console.log('Kullanıcı veritabanından silindi:', data);
    return data;
  })
  .catch(error => {
    console.error('Webhook çağrısı başarısız:', error);
    throw error;
  });
}); 
