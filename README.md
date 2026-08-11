# GitHub API

Django REST Framework tabanlı, GitHub'a benzer bir kullanıcı / repository / organizasyon yönetim API'si. Kimlik doğrulama için JWT, API dokümantasyonu için Swagger (OpenAPI) kullanır.

## İçindekiler

- [Özellikler](#özellikler)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Kurulum](#kurulum)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [Docker ile Çalıştırma](#docker-ile-çalıştırma)
- [API Dokümantasyonu](#api-dokümantasyonu)
- [Kimlik Doğrulama](#kimlik-doğrulama)
- [API Uçları](#api-uçları)
  - [Users](#users-apiusers)
  - [Repo](#repo-apirepos)
  - [Organizations](#organizations-apiorganizations)
- [Veri Modelleri](#veri-modelleri)
- [Proje Yapısı](#proje-yapısı)
- [Lisans](#lisans)

## Özellikler

- E-posta tabanlı özel kullanıcı modeli ve JWT ile kimlik doğrulama
- Kişisel veya organizasyona bağlı repository oluşturma ve yönetimi
- Rol tabanlı organizasyon üyeliği (admin / member)
- Admin'e özel kullanıcı ve repository yönetim uçları
- drf-spectacular ile otomatik üretilen OpenAPI şeması, Swagger UI ve ReDoc arayüzü

## Teknoloji Yığını

| Bileşen | Teknoloji |
|---|---|
| Framework | Django 5.2, Django REST Framework |
| Kimlik doğrulama | djangorestframework-simplejwt |
| API şeması | drf-spectacular (OpenAPI 3) |
| Veritabanı | SQLite (varsayılan) |
| WSGI sunucusu | gunicorn |
| Konteynerleştirme | Docker |

## Kurulum

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt

# .env dosyasını oluşturun, bkz. "Ortam Değişkenleri"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sunucu ayağa kalktıktan sonra API `http://127.0.0.1:8000/api/` altında hizmet verir.

## Ortam Değişkenleri

Proje kök dizininde bir `.env` dosyası oluşturun (bu dosya `.gitignore` ile repoya dahil edilmez):

```bash
SECRET_KEY=django-secret-key-buraya
```

## Docker ile Çalıştırma

Proje, `gunicorn` ile 8000 portunda servis veren bir `Dockerfile` içerir.

```bash
docker build -t github-api .

docker run -d \
  --name github-api \
  -p 8000:8000 \
  --env-file .env \
  github-api
```

Konteyner ayağa kalktıktan sonra API `http://localhost:8000/api/` altında erişilebilir olur. İlk çalıştırmada migration ve superuser oluşturma işlemlerini konteyner içinde çalıştırmanız gerekir:

```bash
docker exec -it github-api python manage.py migrate
docker exec -it github-api python manage.py createsuperuser
```

## API Dokümantasyonu

Tüm uçlar `drf-spectacular` ile otomatik olarak belgelenir.

| Yol | Açıklama |
|---|---|
| `/api/schema/` | OpenAPI 3 şeması (JSON) |
| `/api/schema/swagger-ui/` | Swagger UI — uçları interaktif olarak deneyin |
| `/api/schema/redoc/` | ReDoc — salt okunur, referans amaçlı dokümantasyon |

## Kimlik Doğrulama

API, `rest_framework_simplejwt` ile JWT tabanlı kimlik doğrulama kullanır.

1. `POST /api/users/token/` ile e-posta ve şifre göndererek `access` ve `refresh` token alın.
2. İsteklere `Authorization: Bearer <access_token>` başlığını ekleyin.
3. Access token süresi dolduğunda `POST /api/users/token/refresh/` ile yenileyin.

| Token | Ömür |
|---|---|
| Access | 1 saat |
| Refresh | 7 gün |

## API Uçları

### users (`/api/users/`)

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| POST | `signup/` | Kayıt ol | Herkese açık |
| POST | `login/` | Giriş yap | Herkese açık |
| POST | `token/` | JWT access/refresh token al | Herkese açık |
| POST | `token/refresh/` | Access token yenile | Herkese açık |
| POST | `token/verify/` | Token doğrula | Herkese açık |
| GET | `admin/users/` | Kullanıcıları listele | Admin |
| GET/PUT/DELETE | `admin/users/<id>/` | Kullanıcı detayı / güncelleme / silme | Admin |

### repo (`/api/repos/`)

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| GET | `/` | Repoları listele | Giriş yapmış kullanıcı |
| POST | `create/` | Kişisel repo oluştur (owner = istek atan kullanıcı) | Giriş yapmış kullanıcı |
| POST | `organizations/<organization_id>/create/` | Organizasyon repo'su oluştur (owner = null) | Organizasyon üyesi |
| GET | `<id>/` | Repo detayı | Herkese açık |
| PUT | `<id>/update/` | Repo güncelle | Giriş yapmış kullanıcı |
| DELETE | `<id>/delete/` | Repo sil | Giriş yapmış kullanıcı |
| GET | `admin/` | Tüm repoları listele | Admin |
| POST | `admin/create/` | Repo oluştur | Admin |
| GET | `admin/<id>/` | Repo detayı | Admin |
| PUT | `admin/<id>/update/` | Repo güncelle | Admin |
| DELETE | `admin/<id>/delete/` | Repo sil | Admin |

### organizations (`/api/organizations/`)

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| POST | `create/` | Organizasyon oluştur | Giriş yapmış kullanıcı |
| GET | `/` | Organizasyonları listele | Giriş yapmış kullanıcı |
| GET | `<id>/` | Organizasyon detayı | Giriş yapmış kullanıcı |
| PUT | `<id>/update/` | Organizasyon güncelle | Organizasyon admin'i |
| DELETE | `<id>/delete/` | Organizasyon sil | Organizasyon sahibi |
| POST | `<id>/members/` | Üye ekle | Organizasyon admin'i |
| GET | `<organization_id>/members/` | Üyeleri listele | Organizasyon üyesi |
| DELETE | `<organization_id>/members/<id>/remove/` | Üye çıkar | Organizasyon admin'i |

## Veri Modelleri

**CustomUser** — e-posta tabanlı özel kullanıcı modeli (`users.CustomUser`); `email` benzersiz, `slug` e-postadan otomatik üretilir.

**Repo** — bir repo ya bir kullanıcıya (`owner`) ya da bir organizasyona (`organization`) ait olabilir, ikisine birden olamaz; bu kural veritabanı seviyesinde `CheckConstraint` ile garanti altına alınmıştır. Ayrıca görünürlük (`public`/`private`), fork ilişkisi ve varsayılan dal (`default_branch`) alanlarını içerir.

**Organization** — bir sahibi (`owner`) olan, `OrganizationMember` üzerinden `admin`/`member` rolleriyle üyeleri bulunan organizasyon modeli.

## Proje Yapısı

```
githubapi/    # Proje ayarları, URL yönlendirme
users/        # Kullanıcı modeli, kimlik doğrulama, admin kullanıcı yönetimi
repo/         # Repository CRUD işlemleri
organizations/ # Organizasyon ve üyelik yönetimi
```

## Lisans

Bu proje [MIT lisansı](LICENSE) ile lisanslanmıştır.
