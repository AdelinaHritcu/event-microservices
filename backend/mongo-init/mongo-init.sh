#!/usr/bin/env bash
# Runs once, on the first start of an empty data volume (docker-entrypoint-initdb.d).
# Lab 3 – minimal MongoDB hardening:
#   - one user with userAdminAnyDatabase (manages the users of the instance)
#   - for the clients database: one dbOwner user and one readWrite user (used by the app)
set -euo pipefail

echo "### Running mongo-init.sh ###"
echo "Target database: ${MONGO_DB_NAME}"

ROOT_PASS="$(cat "${MONGO_INITDB_ROOT_PASSWORD_FILE}")"
USER_ADMIN_PASS="$(cat /run/secrets/mongo_user_admin_pass)"
OWNER_PASS="$(cat /run/secrets/mongo_db_owner_pass)"
APP_PASS="$(cat /run/secrets/mongo_app_pass)"

mongosh --quiet \
  --username "${MONGO_INITDB_ROOT_USERNAME}" --password "${ROOT_PASS}" --authenticationDatabase admin <<EOF
const dbName = "${MONGO_DB_NAME}";

function ensureUser(database, username, password, roles) {
  if (database.getUser(username)) {
    print("User already exists: " + username + " (skipping)");
    return;
  }
  database.createUser({ user: username, pwd: password, roles: roles });
  print("Created user: " + username);
}

const adminDb = db.getSiblingDB("admin");
const targetDb = db.getSiblingDB(dbName);

ensureUser(adminDb, "${MONGO_USER_ADMIN_USER}", "${USER_ADMIN_PASS}", [ { role: "userAdminAnyDatabase", db: "admin" } ]);
ensureUser(targetDb, "${MONGO_DB_OWNER_USER}", "${OWNER_PASS}", [ { role: "dbOwner", db: dbName } ]);
ensureUser(targetDb, "${MONGO_APP_USER}", "${APP_PASS}", [ { role: "readWrite", db: dbName } ]);
EOF

echo "### mongo-init.sh finished ###"
