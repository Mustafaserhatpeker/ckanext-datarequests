# ckanext-datarequests

Kullanıcıların veri isteklerini oluşturup tartışabildiği bir CKAN eklentisi.

Özellikler:
- Login olmadan listeleme ve detay görüntüleme.
- Login kullanıcılar yeni veri isteği oluşturabilir ve yorum yazabilir.
- Sadece sysadmin kullanıcıları veri isteği durumunu (açık/kapalı) değiştirebilir.
- Login olmadan yeni istek oluşturmaya çalışıldığında popup uyarısı verilir.

## Kurulum

1) Depoyu klonlayın ve kurun (editable mode):
```bash
pip install -e .
```

2) CKAN konfigürasyonuna eklentiyi ekleyin (development.ini, production.ini vb.):
```
ckan.plugins = datarequests
```

3) (Opsiyonel) Veritabanı tabloları ilk yüklemede otomatik oluşturulur. Eğer yetki kısıtı ya da otomatik kurulum devrede değilse, CKAN başlarken hata alırsanız, eklenti aktifken uygulamayı bir kez başlatmanız yeterli olacaktır.

4) Gerekirse statik dosyaların servis edildiğinden emin olun (varsayılan public path eklendi).

## Kullanım

- Liste: /datarequests
- Yeni istek: /datarequests/new
- Detay: /datarequests/<id>

## Geliştirme Notları

- CKAN 2.9+ (Flask) hedeflenmiştir.
- Tablolar otomatik (lazy) oluşturulur; daha kurumsal senaryoda Alembic migration önerilir.