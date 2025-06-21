# PRD – Apartman ve Kapıcı Yönetim Sistemi

## 1. Ürün Tanımı
Bu sistem, apartman yöneticilerinin, sakinlerinin ve görevli/kapıcıların günlük apartman yönetimi ve iletişimini dijitalleştirmesini sağlar.

## 2. Hedef Kitle
- Apartman yöneticileri
- Apartman sakinleri (daire sahipleri & kiracılar)
- Kapıcılar / görevli personel

## 3. Temel Özellikler

### Kullanıcı Sistemi
- Rol bazlı giriş (Yönetici, Daire Sakini, Kapıcı)
- Kullanıcılar kendi daireleriyle ilişkili verileri görür
- Yetki kontrollü admin panel

### Apartman ve Daire Bilgisi
- Apartman tanımı (isim, blok, adres)
- Daire bilgileri ve kullanıcı eşlemesi

### Aidat Yönetimi
- Aidat oluşturma (yönetici)
- Ödeme durumu takibi
- Gecikme faizi hesaplama
- Online ödeme (opsiyonel)

### Gider & Raporlama
- Gider girişi
- Belge yükleme
- Grafiksel raporlar
- Yıllık PDF raporlar

### Duyuru Sistemi
- Yönetici duyuru girişi
- Tüm sakinlere bildirim
- Okundu işaretleme

### Şikayet ve Destek Sistemi
- Daire sakinleri tarafından şikayet oluşturulabilir
- Yönetici ve kapıcı yanıt verebilir
- Durum takibi ve zaman damgası

### Kapıcı Paneli
- Günlük görev takibi
- Görev tamamlama ve dosya/fotoğraf yükleme
- Bildirim sistemi

### Paket ve Ziyaretçi Takibi
- Kapıcı gelen paketleri kaydedebilir
- Kullanıcılar teslim alabilir
- Ziyaretçi girişleri izlenebilir (isteğe bağlı)

## 4. Teknik Gereksinimler
- Python 3.11+, Django 4.x
- Django Rest Framework (API)
- TailwindCSS veya Bootstrap
- PostgreSQL
- JWT veya Session-based Auth
- AWS S3 veya benzeri dosya yükleme (opsiyonel)

## 5. Performans ve Güvenlik
- Rate-limiting
- Giriş denemesi sınırlandırma
- Günlük yedekleme
- HTTPS zorunluluğu

## 6. Versiyonlama ve Yol Haritası
- v1.0: Minimum özelliklerle MVP çıkışı
- v1.1: Online ödeme entegrasyonu
- v1.2: Mobil uyumluluk ve PWA desteği
