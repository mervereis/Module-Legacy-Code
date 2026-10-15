# PurpleForest: Başka bir Mac'te kurulum (v2, sade)

Veritabanı Docker ile çalışır, backend ve front-end yerelde çalışır. `psql` kurmana gerek yok, şema Docker container'ının içinden yüklenir.

Tüm komutlar macOS Terminal'de (zsh) çalışır. `<...>` kısımlarını kendine göre değiştir.

## Önkoşullar (bir kez)

1. **Git** kurulu olmalı.
2. **Python 3.13** kurulu olmalı. Python 3.14 çalışmaz (`psycopg2-binary` ve `cffi` için hazır paket yok, `pg_config not found` hatası çıkar).
   - Kontrol: `python3.13 --version`
   - macOS 13 (Ventura) ve eski sürümlerde `brew install python@3.13` çok uzun sürer (Homebrew hazır paket vermiyor). Bunun yerine https://www.python.org/downloads/macos/ adresinden **3.13.x** "universal2 installer"ı indirip kur. Sonra Terminal'i kapatıp aç.
3. **Docker Desktop** kurulu ve **açık** olmalı. Menü çubuğundaki balina simgesi sabitlenene kadar bekle. Kontrol: `docker info` hata vermemeli.

## Bir kez yapılacaklar

### 1. Projeyi indir
```bash
git clone <repo-url> ~/Module-Legacy-Code
cd ~/Module-Legacy-Code
git checkout sprint2-rebloom
```
Not: Commit edilmemiş değişiklikler (ör. `main.py`'deki `/rebloom` route eklemesi, `schema.sql`) yeni Mac'te olmaz. Önce commit edip push et.

### 2. `.env` dosyasını oluştur
`.env` git'e girmediği için yeni Mac'te yok:
```bash
cd ~/Module-Legacy-Code/backend
cat > .env <<EOF
JWT_SECRET_KEY=herhangi-uzun-rastgele-bir-yazi
POSTGRES_PASSWORD=herhangi-bir-sifre
POSTGRES_USER=postgres
EOF
```

### 3. Python ortamını kur
```bash
cd ~/Module-Legacy-Code/backend
python3.13 -m venv .venv
. .venv/bin/activate
python --version        # 3.13.x yazmalı
pip install -r requirements.txt
```

### 4. Veritabanını başlat (Terminal 1)
```bash
cd ~/Module-Legacy-Code/db
./run.sh
```
`./run.sh` izin hatası verirse önce `chmod +x run.sh` çalıştır.

Bu terminal **açık kalacak**, kapatma. `database system is ready to accept connections` yazısını görene kadar bekle. İlk seferde Postgres image'ı indirileceği için biraz sürer.

### 5. Şemayı yükle (Terminal 2)
```bash
cd ~/Module-Legacy-Code/backend
docker exec -i $(docker ps -q --filter ancestor=postgres:17.4) psql -U postgres < ../db/schema.sql
```
Çıktıda altı tane `CREATE TABLE` yazmalı. `create-schema.sh` kullanma: Mac'te `psql` olmadığı için `psql: command not found` hatası verir.

### 6. Backend'i başlat (Terminal 2)
```bash
cd ~/Module-Legacy-Code/backend
. .venv/bin/activate
python3 main.py
```
Bu terminal de açık kalacak. Backend `http://127.0.0.1:3000` adresinde çalışır.

### 7. Örnek veriyi yükle (Terminal 3, backend çalışırken)
```bash
cd ~/Module-Legacy-Code/backend
. .venv/bin/activate
python3 populate.py
```
`populate.py` backend'in API'sine istek attığı için backend (Adım 6) çalışıyor olmalı. **İki kere çalıştırma**, kullanıcılar zaten varsa hata verir.

### 8. Front-end'i başlat (Terminal 3 veya 4)
```bash
cd ~/Module-Legacy-Code/front-end
python3 -m http.server 8000
```

### 9. Tarayıcıda aç
- Adres: **http://localhost:8000**
- Giriş: kullanıcı `sample`, şifre `sosecret`
- Adres `localhost:8000` veya `127.0.0.1:8000` olmalı. Backend'in CORS ayarı sadece bu iki kökene izin veriyor.

## Sonraki çalıştırmalar

Docker Desktop açıkken, 3 terminalde:

| Terminal | Komut |
|---|---|
| 1 | `cd ~/Module-Legacy-Code/db && ./run.sh` |
| 2 | `cd ~/Module-Legacy-Code/backend && . .venv/bin/activate && python3 main.py` |
| 3 | `cd ~/Module-Legacy-Code/front-end && python3 -m http.server 8000` |

Şema ve örnek veri `db/pg_data` içinde kalıcıdır, tekrar yüklemene gerek yok.

## Durdurma ve sıfırlama

- Her terminalde `Ctrl+C`. Veritabanı terminalinde `Ctrl+C` container'ı durdurur, veri silinmez.
- Her şeyi sıfırlamak için: veritabanını durdur, `rm -rf ~/Module-Legacy-Code/db/pg_data` çalıştır, sonra Adım 4, 5, 6, 7'yi tekrarla.

## Veritabanını VS Code'dan görmek (isteğe bağlı)

VS Code'a bir PostgreSQL eklentisi kur (ör. "PostgreSQL" veya "SQLTools" + SQLTools PostgreSQL Driver). Veritabanı çalışırken yeni bağlantı ekle:

| Alan | Değer |
|---|---|
| Host | `localhost` |
| Port | `5432` |
| Kullanıcı | `postgres` |
| Şifre | `.env`'deki `POSTGRES_PASSWORD` |
| Veritabanı | `postgres` |

`public` şemasında `users`, `blooms`, `follows`, `hashtags`, `reblooms` tablolarını görürsün. Eklenti sadece istemcidir, veritabanı Docker'da çalışmaya devam etmelidir.

## Olası sorunlar

- **`pg_config executable not found` / `Failed to build psycopg2_binary` (Adım 3):** Python 3.14 kullanıyorsun. `deactivate; rm -rf .venv; python3.13 -m venv .venv` ile 3.13'te yeniden kur.
- **`psql: command not found`:** `create-schema.sh` yerine Adım 5'teki `docker exec` komutunu kullan.
- **`port is already allocated` (5432):** Başka bir Postgres çalışıyor (ya da eski bir container). `docker ps` ile bak, gerekirse `docker stop <container-id>`.
- **Adım 5'te `docker exec` boş container hatası verirse:** Adım 4'teki veritabanı çalışmıyor demektir. Terminal 1'i kontrol et.
- **Port 3000 meşgul:** `lsof -i :3000` ile bak.
- **Giriş yapamıyorum / veri yok:** Adım 7 (`populate.py`) yapılmamış olabilir.
