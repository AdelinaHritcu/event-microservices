#!/usr/bin/env bash
set -euo pipefail

echo "### Running mongo-init.sh ###"
echo "Target database: ${MONGO_DB_NAME}"

OWNER_PASS="$(cat /run/secrets/mongo_db_owner_pass)"
APP_PASS="$(cat /run/secrets/mongo_app_pass)"

mongosh --quiet <<EOF
use admin;

const dbName = "${MONGO_DB_NAME}";
const ownerUser = "${MONGO_DB_OWNER_USER}";
const ownerPass = "${OWNER_PASS}";
const appUser = "${MONGO_APP_USER}";
const appPass = "${APP_PASS}";

const targetDb = db.getSiblingDB(dbName);

function ensureUser(username, password, roles) {
  const existing = targetDb.getUser(username);
  if (existing) {
    print("User already exists: " + username + " (skipping)");
    return;
  }
  targetDb.createUser({
    user: username,
    pwd: password,
    roles: roles
  });
  print("Created user: " + username);
}

ensureUser(ownerUser, ownerPass, [ { role: "dbOwner", db: dbName } ]);
ensureUser(appUser, appPass, [ { role: "readWrite", db: dbName } ]);
EOF

echo "### mongo-init.sh finished ###"
