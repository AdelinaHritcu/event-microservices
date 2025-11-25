#!/bin/bash
set -e

echo "### Running mongo-init.sh ###"
echo "Creating db users for database: ${MONGO_DB_NAME}"

mongosh <<EOF
use admin;
db = db.getSiblingDB("${MONGO_DB_NAME}");
db.createUser({
  user: "${MONGO_DB_OWNER_USER}",
  pwd: "${MONGO_DB_OWNER_PASS}",
  roles: [ { role: "dbOwner", db: "${MONGO_DB_NAME}" } ]
});
db.createUser({
  user: "${MONGO_APP_USER}",
  pwd: "${MONGO_APP_PASS}",
  roles: [ { role: "readWrite", db: "${MONGO_DB_NAME}" } ]
});
EOF

echo "### mongo-init.sh finished ###"
