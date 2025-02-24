import psycopg2
from dotenv import load_dotenv
import os

load_dotenv("db.env")
DATABASE_URL = os.getenv("DATABASE_URL")

DROP_SCRIPT = "migrations/004_drop_tables.sql"


def execute_script(cursor, file_path):
    with open(file_path, "r") as file:
        sql = file.read()
        cursor.execute(sql)


def main():
    if not DATABASE_URL:
        print("DATABASE_URL is not set. Please check your db.env file.")
        return

    try:
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        print(f"Executing drop script: {DROP_SCRIPT}")
        execute_script(cursor, DROP_SCRIPT)
        connection.commit()

        print("All tables dropped successfully.")
    except Exception as e:
        print(f"An error occurred while dropping tables: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


if __name__ == "__main__":
    main()
