#!/usr/bin/env bash
set -euo pipefail

echo "Initializing extra MariaDB users..."

ROOT_PASS="$(cat /run/secrets/db_root_pass)"
ADMIN_USER="${DB_ADMIN_USER:?Missing DB_ADMIN_USER}"
ADMIN_PASS="$(cat /run/secrets/db_admin_pass)"
APP_USER="${DB_USER:?Missing DB_USER}"
APP_PASS="$(cat /run/secrets/db_user_pass)"
DB_NAME="${DB_NAME:?Missing DB_NAME}"

mysql -uroot -p"${ROOT_PASS}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`;

CREATE USER IF NOT EXISTS '${ADMIN_USER}'@'%' IDENTIFIED BY '${ADMIN_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${ADMIN_USER}'@'%';

CREATE USER IF NOT EXISTS '${APP_USER}'@'%' IDENTIFIED BY '${APP_PASS}';
GRANT SELECT, INSERT, UPDATE, DELETE ON \`${DB_NAME}\`.* TO '${APP_USER}'@'%';

FLUSH PRIVILEGES;
SQL

echo "MariaDB users initialized."
