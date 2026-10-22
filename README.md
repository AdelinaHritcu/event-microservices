# POS - solutii proiect

| **Deadline&nbsp;general** | **_18.01.2026_** (_duminica, S14_) |
| :--- | :--- |
| **_Branch_ proiect** | Acest _branch_ va fi folosit de studentii care doresc sa dezvolte proiectul propus pentru disciplina. _Commit_-urile trebuie realizate saptamanal. Codurile sursa vor fi organizate pe module, iar in cadrul fiecauri astfel de modul se vor incarca un set de _log_-uri demonstrative. |
| **_Branch_&nbsp;laborator** | Acest _branch_ va fi folosit de studentii care se vor concentra doar pe aplicatiile de baza propuse. Pentru fiecare laborator se va crea cate un director separat in cadrul caruia se vor incarca fisierele sursa, alaturi de un set de _log_-uri demonstrative.<br/><br/>**_Fiecare laborator are un deadline de maxim doua saptamani de la data finalizarii acestuia!! Commit-urile ulterioare NU vor fi considerate in evaluare_** |

## Evaluare

Evaluarea activitatii de laborator consta in evaluarea solutiilor incarcate, urmarind:

- respectarea standardelor si a recomandarilor corespuzatoare tipului de serviciu analizat;
- calitatea codului sursa;
- gradul de indeplinire a cerintelor propuse.

Solutiile **_remarcabile_** pot atrage bonusuri pentru nota de examen/media corespunzatoare disciplinei. **_Revedeti documentul de prezentare a disciplinei, disponibil pe platforma_** <https://edu.tuiasi.ro/>.

## Link-uri utile

1. **Markdown** - limbaj de prezentare "pretty" pentru o documentatie `git` (in cazul in care considerati utila o scurta descriere a implementarii <https://www.markdownguide.org>)
	- sintaxa de baza: <https://www.markdownguide.org/basic-syntax/>
	- _cheat-sheet_: <https://www.markdownguide.org/cheat-sheet/>
2. **Github** - comenzi uzuale: <https://education.github.com/git-cheat-sheet-education.pdf>

---

# Platforma de gestiune a evenimentelor

## Componente

| Container | Rol | Port host |
| :--- | :--- | :--- |
| `pos-idm-service` | IDM, serviciu gRPC (login, validare token, logout, utilizatori) | `50051` |
| `pos-events-manager` | Event WebService, REST (evenimente, pachete, bilete) | `8000` |
| `pos-clients` | Client WebService, REST (clienți, bilete cumpărate, `/auth/*`, `/api/users`) | `8001` |
| `pos-idm-db` | MariaDB pentru utilizatorii IDM | – |
| `pos-mariadb` | MariaDB pentru evenimente / pachete / bilete | – |
| `pos-mongo` | MongoDB pentru documentele clienților | – |

Documentația OpenAPI: `http://localhost:8000/docs`, `http://localhost:8001/docs`
(rutele protejate cer header-ul `Authorization: Bearer <JWS>`).

## Pregătire (o singură dată)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1   # Windows
./scripts/setup.sh                                           # Linux / macOS / Git Bash
```

Scriptul creează `.env` (din `.env.example`), parolele în `secrets/*.txt` și certificatul TLS
al serviciului IDM în `certs/` (openssl rulează într-un container, nu trebuie instalat).
`.env`, `secrets/` și cheile din `certs/` nu se pun în git.

## Rulare cu Docker Compose

```bash
docker compose up --build
```

Ordinea de pornire este impusă prin `depends_on` + `healthcheck`: baza de date, apoi serviciul.
Dacă ai rulat o versiune mai veche (cu alte parole), șterge volumele: `docker compose down -v`.

## Rulare manuală (`docker network` + `docker run`)

Numele simbolice ale containerelor de baze de date sunt cele din `.env`
(`EVENTS_DB_CONTAINER`, `CLIENTS_DB_CONTAINER`, `IDM_DB_CONTAINER`) și sunt transmise serviciilor
prin variabile de mediu. Exemplu PowerShell, din rădăcina proiectului, după `scripts\setup.ps1`:

```powershell
Get-Content .env | Where-Object { $_ -match '^\w+=' } | ForEach-Object { $k,$v = $_ -split '=',2; Set-Item "env:$k" $v }
$S = "${PWD}\secrets"; $C = "${PWD}\certs"

# 1. rețeaua virtuală
docker network create pos-network

# 2. bazele de date (primele)
docker run -d --name $env:IDM_DB_CONTAINER --network pos-network `
  -e MARIADB_DATABASE=$env:IDM_DB_NAME -e MARIADB_USER=$env:IDM_DB_USER `
  -e MARIADB_PASSWORD_FILE=/run/secrets/idm_db_pass -e MARIADB_ROOT_PASSWORD_FILE=/run/secrets/idm_db_root_pass `
  -v "${S}:/run/secrets:ro" mariadb:11

docker run -d --name $env:EVENTS_DB_CONTAINER --network pos-network `
  -e MYSQL_DATABASE=$env:DB_NAME -e MYSQL_USER=$env:DB_USER -e DB_NAME=$env:DB_NAME -e DB_USER=$env:DB_USER -e DB_ADMIN_USER=$env:DB_ADMIN_USER `
  -e MYSQL_PASSWORD_FILE=/run/secrets/db_user_pass -e MYSQL_ROOT_PASSWORD_FILE=/run/secrets/db_root_pass `
  -v "${S}:/run/secrets:ro" -v "${PWD}\backend\mariadb-init:/docker-entrypoint-initdb.d:ro" mariadb:11

docker run -d --name $env:CLIENTS_DB_CONTAINER --network pos-network `
  -e MONGO_INITDB_ROOT_USERNAME=$env:MONGO_ADMIN_USER -e MONGO_INITDB_ROOT_PASSWORD_FILE=/run/secrets/mongo_admin_pass `
  -e MONGO_DB_NAME=$env:MONGO_DB_NAME -e MONGO_DB_OWNER_USER=$env:MONGO_DB_OWNER_USER -e MONGO_APP_USER=$env:MONGO_APP_USER `
  -v "${S}:/run/secrets:ro" -v "${PWD}\backend\mongo-init:/docker-entrypoint-initdb.d:ro" mongo:8 mongod --auth

# 3. imaginile serviciilor
docker build -t pos-idm ./backend/idm-service
docker build -t pos-events ./backend/events-manager-service
docker build -t pos-clients ./backend/clients-service

# 4. serviciile (după ce bazele de date au pornit)
docker run -d --name pos-idm-service --network pos-network -p 50051:50051 `
  -e IDM_DB_HOST=$env:IDM_DB_CONTAINER -e IDM_DB_NAME=$env:IDM_DB_NAME -e IDM_DB_USER=$env:IDM_DB_USER -e IDM_DB_PASS_FILE=/run/secrets/idm_db_pass `
  -e IDM_JWT_SECRET=$env:IDM_JWT_SECRET -e IDM_JWT_ISSUER=$env:IDM_JWT_ISSUER -e IDM_TLS_CERT=/certs/idm.crt -e IDM_TLS_KEY=/certs/idm.key `
  -v "${S}:/run/secrets:ro" -v "${C}:/certs:ro" pos-idm

docker run -d --name pos-events-manager --network pos-network -p 8000:8000 --user 0:0 `
  -e DB_HOST=$env:EVENTS_DB_CONTAINER -e DB_NAME=$env:DB_NAME -e DB_USER=$env:DB_USER -e DB_PASS_FILE=/run/secrets/db_user_pass `
  -e IDM_GRPC_HOST=pos-idm-service -e IDM_TLS_ROOT_CERT=/certs/idm.crt -e CLIENTS_PUBLIC_URL=$env:CLIENTS_PUBLIC_URL `
  -v "${S}:/run/secrets:ro" -v "${C}:/certs:ro" pos-events

docker run -d --name pos-clients --network pos-network -p 8001:8000 `
  -e MONGO_HOST=$env:CLIENTS_DB_CONTAINER -e MONGO_DB_NAME=$env:MONGO_DB_NAME -e MONGO_APP_USER=$env:MONGO_APP_USER -e MONGO_APP_PASS_FILE=/run/secrets/mongo_app_pass `
  -e MONGO_CLIENTS_COLLECTION=$env:MONGO_CLIENTS_COLLECTION -e IDM_GRPC_HOST=pos-idm-service -e IDM_TLS_ROOT_CERT=/certs/idm.crt `
  -e DATA_SERVICE_URL=http://pos-events-manager:8000 -e EVENTS_PUBLIC_URL=$env:EVENTS_PUBLIC_URL `
  -v "${S}:/run/secrets:ro" -v "${C}:/certs:ro" pos-clients
```

Oprire: `docker rm -f pos-clients pos-events-manager pos-idm-service pos-mongo pos-mariadb pos-idm-db; docker network rm pos-network`.

## Conturi de test

| Email | Parolă | Rol |
| :--- | :--- | :--- |
| `admin@test.com` | `admin123` | admin |
| `owner@test.com` | `owner123` | owner-event |
| `client@test.com` | `client123` | client |

Alte conturi le creează administratorul: `POST http://localhost:8001/api/users`
(`{"email": "...", "password": "...", "role": "client" | "owner-event"}`). Pentru rolul `client`
se creează automat și documentul MongoDB (legătura utilizator–client se face prin `email`).

## Roluri

| Rol | Poate |
| :--- | :--- |
| vizitator (fără login) | vede evenimentele și pachetele (rutele `GET` publice din Event WebService) |
| admin | gestionează utilizatorii (`/api/users`) și datele clienților (`/api/clients`); nu are acces la evenimente / bilete |
| owner-event | gestionează complet evenimentele / pachetele proprii (`ID_OWNER` = `sub` din JWS), vede evenimentele celorlalți, vede datele publice ale cumpărătorilor (`/api/clients/buyers`) |
| client | își gestionează profilul (`/api/clients/me`), vede evenimentele și pachetele, cumpără și validează bilete (`/api/clients/me/tickets`) |

Toate celelalte rute cer `Authorization: Bearer <JWS>`: 401 fără token / token invalid, 403 dacă rolul nu are drept.
`PUT` pe o resursă existentă întoarce `204 No Content`.

## CORS

Ambele servicii REST acceptă cereri cross-origin doar de la originile din `CORS_ORIGINS`
(implicit `http://localhost:5173,http://127.0.0.1:5173`), cu metodele `GET, POST, PUT, DELETE`
și header-ele `Authorization, Content-Type, Accept`.

## Frontend (ReactJS, laboratorul 6)

```bash
cd frontend/pos-web
cp .env.example .env
npm install
npm run dev     # http://localhost:5173
```

| Rol | Pagini |
| :--- | :--- |
| vizitator | Events, Packages (căutare + paginare prin API) |
| owner-event | My events, My packages (creare / editare / ștergere, evenimente din pachet, bilete vândute), Buyers, All events / packages |
| client | Events, Packages (cumpărare bilete), My tickets (validare), Profile |
| admin | Users (creare / ștergere conturi), Clients |
