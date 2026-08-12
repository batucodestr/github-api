# GitHub API

Django REST Framework tabanlı, GitHub'ın temel çalışma mantığını taklit eden açık kaynak bir backend API'si. Kullanıcı, repository, organizasyon yönetiminin yanı sıra star, fork, branch, commit, issue, pull request, organizasyon daveti ve takım (team) sistemlerini içerir. Kimlik doğrulama için JWT, API dokümantasyonu için Swagger (OpenAPI) kullanır.

## İçindekiler

- [Özellikler](#özellikler)
- [Teknoloji Yığını](#teknoloji-yığını)
- [Kurulum](#kurulum)
- [Ortam Değişkenleri](#ortam-değişkenleri)
- [Docker ile Çalıştırma](#docker-ile-çalıştırma)
- [API Dokümantasyonu](#api-dokümantasyonu)
- [Kimlik Doğrulama](#kimlik-doğrulama)
- [Filtreleme, Arama, Sıralama ve Sayfalama](#filtreleme-arama-sıralama-ve-sayfalama)
- [Rate Limiting](#rate-limiting)
- [API Uçları](#api-uçları)
  - [Users](#users-apiusers)
  - [Repo](#repo-apirepos)
  - [Organizations](#organizations-apiorganizations)
  - [Search](#search-apisearch)
- [Veri Modelleri](#veri-modelleri)
- [Proje Yapısı](#proje-yapısı)
- [Testler](#testler)
- [Lisans](#lisans)

## Özellikler

- E-posta tabanlı özel kullanıcı modeli ve JWT ile kimlik doğrulama
- Kişisel veya organizasyona bağlı repository oluşturma ve yönetimi
- Rol tabanlı organizasyon üyeliği (admin / member)
- **Stars** — repository yıldızlama, yıldız kaldırma, yıldız sayısı ve yıldızlayanlar listesi
- **Forks** — repository fork'lama (kişisel veya organizasyon adına), parent/fork ilişkisi
- **Branches** — dal oluşturma, listeleme, silme, varsayılan dal belirleme
- **Commits** — simüle edilmiş commit geçmişi (repository ve dal bazlı)
- **Issues** — issue oluşturma/güncelleme/kapatma/yeniden açma/silme + yorumlar
- **Pull Requests** — PR oluşturma/güncelleme/kapatma/yeniden açma + yorumlar, kaynak/hedef dal doğrulaması
- **Organization Invitations** — kullanıcı davet etme, kabul/red, bekleyen davet tekilliği
- **Teams** — organizasyon içi takım, takım üyeliği ve takımın erişebildiği repository yönetimi
- **Search** — repository isim/açıklama üzerinde arama (`/api/search/repositories/?q=...`)
- **Filtering / Sorting / Pagination** — django-filter ve güvenli alan listesiyle sıralama, sayfalanmış liste response'ları
- **Rate limiting** — anonim/kimliği doğrulanmış kullanıcılar için farklı throttle oranları, login/signup için özel sınır
- **Caching** — repository, organizasyon ve kullanıcı detay uçlarında kısa süreli cache
- Tutarlı hata response formatı (`detail` / `errors`) ve uygun HTTP durum kodları
- Admin'e özel kullanıcı ve repository yönetim uçları
- drf-spectacular ile otomatik üretilen OpenAPI şeması, Swagger UI ve ReDoc arayüzü

## Teknoloji Yığını

| Bileşen | Teknoloji |
|---|---|
| Framework | Django 5.2, Django REST Framework |
| Kimlik doğrulama | djangorestframework-simplejwt |
| Filtreleme | django-filter |
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

Proje, `gunicorn` ile 8000 portunda servis veren bir `Dockerfile` ve tek komutla ayağa kaldırmak için bir `docker-compose.yml` içerir. `docker-compose.yml`, konteyner başlarken migration'ları otomatik uygular; `db.sqlite3` ve `logs/` kalıcı olacak şekilde bağlanır.

`.env` dosyasının kök dizinde bulunduğundan emin olun (bkz. [Ortam Değişkenleri](#ortam-değişkenleri)), ardından:

```bash
docker compose up --build
```

Konteyner ayağa kalktıktan sonra API `http://localhost:8000/api/` altında erişilebilir olur. Superuser oluşturmak için:

```bash
docker compose exec web python manage.py createsuperuser
```

Arka planda çalıştırmak için `docker compose up --build -d`, durdurmak için `docker compose down` kullanabilirsiniz.

Compose olmadan doğrudan Docker ile çalıştırmak isterseniz:

```bash
docker build -t github-api .

docker run -d \
  --name github-api \
  -p 8000:8000 \
  --env-file .env \
  github-api

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

## Filtreleme, Arama, Sıralama ve Sayfalama

Repo listesi (`GET /api/repos/`) aşağıdaki sorgu parametrelerini destekler:

| Parametre | Açıklama | Örnek |
|---|---|---|
| `visibility` | `public` / `private` filtrele | `?visibility=public` |
| `owner` | Sahip kullanıcı id'sine göre filtrele | `?owner=3` |
| `organization` | Organizasyon id'sine göre filtrele | `?organization=1` |
| `is_fork` | Fork olup olmama durumuna göre filtrele | `?is_fork=true` |
| `ordering` | `name`, `created_at`, `updated_at`, `stars_count` alanlarına göre sırala (`-` ile azalan) | `?ordering=-stars_count` |
| `page` | Sayfa numarası (sayfa başına 20 kayıt) | `?page=2` |

Tüm liste uçları `{"count", "next", "previous", "results"}` yapısında sayfalanmış response döner.

## Rate Limiting

| Kullanıcı türü | Oran |
|---|---|
| Anonim (giriş yapmamış) | 100/saat |
| Kimliği doğrulanmış kullanıcı | 1000/saat |
| `signup` / `login` / `token/` | 20/saat (kötüye kullanım riski yüksek uçlar için özel sınır) |

## API Uçları

### users (`/api/users/`)

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| POST | `signup/` | Kayıt ol | Herkese açık |
| POST | `login/` | Giriş yap | Herkese açık |
| POST | `token/` | JWT access/refresh token al | Herkese açık |
| POST | `token/refresh/` | Access token yenile | Herkese açık |
| POST | `token/verify/` | Token doğrula | Herkese açık |
| GET | `<id>/` | Herkese açık kullanıcı profili (cache'li) | Herkese açık |
| GET | `admin/users/` | Kullanıcıları listele | Admin |
| GET/PUT/DELETE | `admin/users/<id>/` | Kullanıcı detayı / güncelleme / silme | Admin |

### repo (`/api/repos/`)

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| GET | `/` | Repoları listele (filtre/sıralama destekli) | Herkese açık (private sadece sahibi/org üyesine görünür) |
| POST | `create/` | Kişisel repo oluştur (owner = istek atan kullanıcı) | Giriş yapmış kullanıcı |
| POST | `organizations/<organization_id>/create/` | Organizasyon repo'su oluştur (owner = null) | Organizasyon üyesi |
| GET | `starred/` | Giriş yapmış kullanıcının yıldızladığı repolar | Giriş yapmış kullanıcı |
| GET | `<id>/` | Repo detayı (cache'li) | Herkese açık (görünürlük kuralına tabi) |
| PUT | `<id>/update/` | Repo güncelle | Repo sahibi |
| DELETE | `<id>/delete/` | Repo sil | Repo sahibi |
| POST | `<id>/star/` | Repoyu yıldızla | Giriş yapmış kullanıcı |
| DELETE | `<id>/unstar/` | Yıldızı kaldır | Giriş yapmış kullanıcı |
| GET | `<id>/stargazers/` | Repoyu yıldızlayanları listele | Herkese açık |
| POST | `<id>/fork/` | Repoyu fork'la (kişisel veya `organization` id'siyle) | Giriş yapmış kullanıcı |
| GET | `<id>/forks/` | Repo'nun fork'larını listele | Herkese açık |
| GET/POST | `<id>/branches/` | Dalları listele / dal oluştur | GET herkese açık, POST repo sahibi/org üyesi |
| GET/DELETE | `<id>/branches/<branch_id>/` | Dal detayı / dal sil | GET herkese açık, DELETE repo sahibi/org üyesi |
| POST | `<id>/branches/<branch_id>/set-default/` | Dalı varsayılan yap | Repo sahibi/org üyesi |
| GET/POST | `<id>/commits/` | Repo commit geçmişi / commit oluştur | GET herkese açık, POST repo sahibi/org üyesi |
| GET | `<id>/branches/<branch_id>/commits/` | Dal commit geçmişi | Herkese açık |
| GET | `<id>/commits/<commit_id>/` | Commit detayı | Herkese açık |
| GET/POST | `<id>/issues/` | Issue'ları listele / oluştur | Giriş yapmış kullanıcı |
| GET/PUT/DELETE | `<id>/issues/<issue_id>/` | Issue detayı / güncelle / sil | Yazar veya repo sahibi/org üyesi |
| POST | `<id>/issues/<issue_id>/close/` | Issue kapat | Yazar veya repo sahibi/org üyesi |
| POST | `<id>/issues/<issue_id>/reopen/` | Issue yeniden aç | Yazar veya repo sahibi/org üyesi |
| GET/POST | `<id>/issues/<issue_id>/comments/` | Issue yorumları listele / oluştur | Giriş yapmış kullanıcı |
| PUT/DELETE | `<id>/issues/<issue_id>/comments/<comment_id>/` | Yorum güncelle / sil | Yorumun yazarı |
| GET/POST | `<id>/pulls/` | PR'ları listele / oluştur | Giriş yapmış kullanıcı |
| GET/PUT | `<id>/pulls/<pr_id>/` | PR detayı / güncelle | Yazar veya repo sahibi/org üyesi |
| POST | `<id>/pulls/<pr_id>/close/` | PR kapat | Yazar veya repo sahibi/org üyesi |
| POST | `<id>/pulls/<pr_id>/reopen/` | PR yeniden aç | Yazar veya repo sahibi/org üyesi |
| GET/POST | `<id>/pulls/<pr_id>/comments/` | PR yorumları listele / oluştur | Giriş yapmış kullanıcı |
| PUT/DELETE | `<id>/pulls/<pr_id>/comments/<comment_id>/` | Yorum güncelle / sil | Yorumun yazarı |
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
| GET | `<id>/` | Organizasyon detayı (cache'li) | Giriş yapmış kullanıcı |
| PUT | `<id>/update/` | Organizasyon güncelle | Organizasyon admin'i |
| DELETE | `<id>/delete/` | Organizasyon sil | Organizasyon sahibi |
| POST | `<id>/members/` | Üye ekle | Organizasyon admin'i |
| GET | `<organization_id>/members/` | Üyeleri listele | Organizasyon üyesi |
| DELETE | `<organization_id>/members/<id>/remove/` | Üye çıkar | Organizasyon admin'i |
| POST | `<organization_id>/invitations/` | Kullanıcıyı organizasyona davet et | Organizasyon admin'i |
| GET | `invitations/` | Giriş yapmış kullanıcının aldığı davetler | Giriş yapmış kullanıcı |
| POST | `invitations/<id>/accept/` | Daveti kabul et | Davet edilen kullanıcı |
| POST | `invitations/<id>/reject/` | Daveti reddet | Davet edilen kullanıcı |
| GET/POST | `<organization_id>/teams/` | Takımları listele / oluştur | GET org üyesi, POST org admin'i |
| GET/DELETE | `<organization_id>/teams/<team_id>/` | Takım detayı / sil | GET org üyesi, DELETE org admin'i |
| GET/POST | `<organization_id>/teams/<team_id>/members/` | Takım üyelerini listele / ekle | GET org üyesi, POST org admin'i |
| DELETE | `<organization_id>/teams/<team_id>/members/<id>/remove/` | Takımdan üye çıkar | Organizasyon admin'i |
| GET/POST | `<organization_id>/teams/<team_id>/repositories/` | Takımın erişebildiği repoları listele / ekle | GET org üyesi, POST org admin'i |
| DELETE | `<organization_id>/teams/<team_id>/repositories/<id>/remove/` | Takımın repo erişimini kaldır | Organizasyon admin'i |

### search (`/api/search/`)

| Yöntem | Yol | Açıklama | Yetki |
|---|---|---|---|
| GET | `repositories/?q=<terim>` | Repository isim ve açıklamasında arama yapar | Herkese açık (görünürlük kuralına tabi) |

## Veri Modelleri

**CustomUser** — e-posta tabanlı özel kullanıcı modeli (`users.CustomUser`); `email` benzersiz, `slug` e-postadan otomatik üretilir.

**Repo** — bir repo ya bir kullanıcıya (`owner`) ya da bir organizasyona (`organization`) ait olabilir, ikisine birden olamaz; bu kural veritabanı seviyesinde `CheckConstraint` ile garanti altına alınmıştır. Görünürlük (`public`/`private`), fork ilişkisi (`is_fork`, `fork_parent`) ve varsayılan dal (`default_branch`) alanlarını içerir.

**Star** — kullanıcı ile repository arasındaki yıldızlama ilişkisi; `(user, repository)` çifti `UniqueConstraint` ile tekil tutulur.

**Branch** — repository'ye bağlı dal; `(repository, name)` çifti `UniqueConstraint` ile tekildir, `is_default` alanı varsayılan dalı işaretler.

**Commit** — simüle edilmiş commit; repository, dal, yazar, mesaj ve otomatik üretilen `hash` alanlarını içerir.

**Issue / IssueComment** — repository'ye bağlı issue takibi; `status` (`open`/`closed`) ve yorum sistemi.

**PullRequest / PullRequestComment** — kaynak ve hedef dal arasındaki değişiklik teklifi; `status` (`open`/`closed`/`merged`), kaynak/hedef dalın aynı repository'ye ait olması doğrulanır.

**Organization** — bir sahibi (`owner`) olan, `OrganizationMember` üzerinden `admin`/`member` rolleriyle üyeleri bulunan organizasyon modeli.

**OrganizationInvitation** — bir kullanıcının organizasyona davet edilme kaydı; `status` (`pending`/`accepted`/`rejected`), aynı kullanıcı için bekleyen davet tekilliği `UniqueConstraint` ile korunur.

**Team / TeamMember / TeamRepository** — organizasyon içi takım yapısı; takım üyeleri organizasyon üyesi olmak zorundadır, takımın erişebildiği repository'ler o organizasyona ait olmalıdır.

## Proje Yapısı

```
githubapi/    # Proje ayarları, URL yönlendirme, özel exception handler
users/        # Kullanıcı modeli, kimlik doğrulama, admin kullanıcı yönetimi
repo/         # Repository, star, fork, branch, commit, issue, pull request
organizations/ # Organizasyon, üyelik, davet ve takım yönetimi
```

## Testler

```bash
python manage.py test
```

Testler özellikle yetkilendirme senaryolarına (sahiplik, organizasyon rolü, private repo görünürlüğü) odaklanır ve `repo`/`organizations` app'lerinde bulunur.

## Lisans

Bu proje [MIT lisansı](LICENSE) ile lisanslanmıştır.
