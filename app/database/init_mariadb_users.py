import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))

DB_NAME = os.getenv("DB_NAME")

ROOT_USER = os.getenv("DB_ROOT_USER")
ROOT_PASS = os.getenv("DB_ROOT_PASS")

ADMIN_USER = os.getenv("DB_ADMIN_USER")
ADMIN_PASS = os.getenv("DB_ADMIN_PASS")

APP_USER = os.getenv("DB_USER")
APP_PASS = os.getenv("DB_PASS")


def run(cur, sql: str):
    print("Running:", sql)
    cur.execute(sql)


def main():
    conn = pymysql.connect(
        host=DB_HOST,
        user=ROOT_USER,
        password=ROOT_PASS,
        port=DB_PORT,
        autocommit=True,
    )
    cur = conn.cursor()

    run(cur, f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
    run(cur, f"USE {DB_NAME};")

    run(cur, f"CREATE USER IF NOT EXISTS '{ADMIN_USER}'@'%' IDENTIFIED BY '{ADMIN_PASS}';")
    run(cur, f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{ADMIN_USER}'@'%';")

    run(cur, f"CREATE USER IF NOT EXISTS '{APP_USER}'@'%' IDENTIFIED BY '{APP_PASS}';")

    run(cur, f"GRANT SELECT, INSERT, UPDATE, DELETE ON {DB_NAME}.Event TO '{APP_USER}'@'%';")
    run(cur, f"GRANT SELECT, INSERT, UPDATE, DELETE ON {DB_NAME}.EventPackage TO '{APP_USER}'@'%';")
    run(cur, f"GRANT SELECT, INSERT, UPDATE, DELETE ON {DB_NAME}.Package TO '{APP_USER}'@'%';")
    run(cur, f"GRANT SELECT, INSERT, UPDATE, DELETE ON {DB_NAME}.Ticket TO '{APP_USER}'@'%';")

    run(cur, "FLUSH PRIVILEGES;")

    cur.close()
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
