# Apartman Yönetim ve Kapıcı Uygulaması – Task Listesi

## 🎯 Amaç
Apartman yönetimi, aidat takibi, şikayet/duyuru bildirimi ve kapıcı görev takibi gibi işlemleri dijitalleştiren, Django tabanlı bir yönetim sistemidir.

---

## 🧱 Modüller

### 1. Kullanıcı Sistemi
- [ ] Giriş / Kayıt olma / Şifre sıfırlama
- [ ] Roller: Yönetici, Daire Sakini, Kapıcı
- [ ] Daire – kullanıcı ilişkisi
- [ ] Kullanıcı profil sayfası

### 2. Apartman ve Daire Yönetimi
- [ ] Apartman oluşturma (isim, blok, adres)
- [ ] Daire tanımı (numara, kat, m², kişi sayısı)
- [ ] Kullanıcıların dairelere atanması
- [ ] Kiracı/sahip ayrımı

### 3. Aidat ve Ödeme Sistemi
- [ ] Aylık aidat oluşturma
- [ ] Aidat listesi & ödeme durumu
- [ ] Gecikme faizi hesaplama
- [ ] Online ödeme entegrasyonu (Stripe, opsiyonel)

### 4. Giderler ve Raporlama
- [ ] Ortak gider kalemleri ekleme
- [ ] Gider belgesi yükleme
- [ ] Aylık/Yıllık finansal raporlar
- [ ] PDF/Excel çıktı desteği

### 5. Duyurular Sistemi
- [ ] Yeni duyuru oluşturma (başlık, açıklama)
- [ ] Kullanıcılara bildirim gönderme
- [ ] Duyuru listesi ve okundu durumu

### 6. Şikayet & Talep Sistemi
- [ ] Şikayet/talep oluşturma
- [ ] Kategori seçimi
- [ ] Durum takibi: Yeni / Devam ediyor / Tamamlandı
- [ ] Yorum ve geri bildirim opsiyonu

### 7. Kapıcı / Görevli Paneli
- [ ] Günlük görev atama
- [ ] Görev güncelleme ve tamamlama
- [ ] Fotoğraf/dosya ekleme
- [ ] Paket teslim kayıtları

### 8. Ziyaretçi ve Paket Bildirimleri
- [ ] Gelen paket kaydı
- [ ] Ziyaretçi giriş bildirimi
- [ ] Kullanıcılara bildirim

### 9. Yönetim Paneli & Loglar
- [ ] Admin panel özelleştirme
- [ ] Aktivite logları
- [ ] Veri yedekleme ve dışa aktarma

### 10. Mobil ve PWA Desteği
- [ ] Mobil uyumlu frontend
- [ ] Ana ekrana eklenebilir PWA desteği (opsiyonel)

---

## 🛠 Teknik Gereklilikler
- Python 3.11+, Django 4+
- Django Rest Framework
- Tailwind CSS (ya da Bootstrap)
- Role-based auth sistemi
- PostgreSQL (tavsiye edilir)
