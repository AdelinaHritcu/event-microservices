#!/usr/bin/env bash
# Same as scripts/setup.ps1, for Linux/macOS/Git Bash.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  jwt=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 48)
  sed -i.bak "s/^IDM_JWT_SECRET=.*/IDM_JWT_SECRET=${jwt}/" .env && rm -f .env.bak
  echo "created .env"
fi

mkdir -p secrets
for n in db_root_pass db_user_pass db_admin_pass mongo_admin_pass mongo_db_owner_pass mongo_app_pass idm_db_root_pass idm_db_pass; do
  f="secrets/$n.txt"
  if [ ! -f "$f" ]; then
    LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 24 > "$f"
    echo "created $f"
  fi
done

if [ ! -f certs/idm.crt ] || [ ! -f certs/idm.key ]; then
  docker run --rm -v "$PWD/certs:/certs" alpine/openssl \
    req -x509 -nodes -newkey rsa:2048 -days 365 \
    -keyout /certs/idm.key -out /certs/idm.crt \
    -config /certs/idm_openssl.cnf -extensions req_ext
  echo "created certs/idm.crt and certs/idm.key"
fi

echo "done. Next: docker compose up --build"
