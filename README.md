# GitHub API

Django REST Framework tabanlı, GitHub'a benzer bir kullanıcı/repo yönetim API'si. JWT ile kimlik doğrulama kullanır.

## Kurulum

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Uygulamalar

- **users** — kayıt/giriş, JWT token işlemleri, admin kullanıcı yönetimi
- **repo** — repo CRUD işlemleri (kullanıcı ve admin uçları)
- **organizations** — organizasyon ve üyelik modelleri

## API Uçları

### users (`/api/users/`)
| Yöntem | Yol | Açıklama |
|---|---|---|
| POST | `signup/` | Kayıt ol |
| POST | `login/` | Giriş yap |
| POST | `token/` | JWT access/refresh token al |
| POST | `token/refresh/` | Access token yenile |
| POST | `token/verify/` | Token doğrula |
| GET | `admin/users/` | Kullanıcıları listele (admin) |
| GET/PUT/DELETE | `admin/users/<id>/` | Kullanıcı detayı (admin) |

### repo (`/api/repos/`)
| Yöntem | Yol | Açıklama |
|---|---|---|
| GET | `/` | Repoları listele |
| POST | `create/` | Kişisel repo oluştur (owner = istek atan kullanıcı) |
| POST | `organizations/<organization_id>/create/` | Organizasyon repo'su oluştur (yalnızca organizasyon üyeleri, owner = null) |
| GET | `<id>/` | Repo detayı |
| PUT | `<id>/update/` | Repo güncelle |
| DELETE | `<id>/delete/` | Repo sil |
| GET/POST/PUT/DELETE | `admin/...` | Admin repo yönetimi |

## Notlar

- Kimlik doğrulama: `rest_framework_simplejwt` (access: 1 saat, refresh: 7 gün)
- Kullanıcı modeli: e-posta tabanlı özel `CustomUser` (`users.CustomUser`)
- Veritabanı: varsayılan olarak SQLite (`db.sqlite3`)
- Repo sahipliği: bir repo ya bir kullanıcıya (`owner`) ya da bir organizasyona (`organization`) ait olabilir, ikisine birden olamaz — bu kural `CheckConstraint` ile veritabanı seviyesinde garanti altına alınmıştır.
