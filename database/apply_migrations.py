import os
import psycopg2
from dotenv import load_dotenv

load_dotenv("db.env")
DATABASE_URL = os.getenv("DATABASE_URL")

MIGRATIONS_DIR = "migrations"

def get_sql_files(directory):
    sql_files = [file for file in os.listdir(directory) if file.endswith(".sql") and "drop" not in file.lower()]
    return sorted(sql_files)


def apply_migration(cursor, file_path):
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

        sql_files = get_sql_files(MIGRATIONS_DIR)
        if not sql_files:
            print("No SQL migration files found in the migrations folder.")
            return

        print("Starting to apply migrations...")

        for sql_file in sql_files:
            file_path = os.path.join(MIGRATIONS_DIR, sql_file)
            print(f"Applying migration: {sql_file}")
            try:
                apply_migration(cursor, file_path)
                connection.commit()
                print(f"Successfully applied: {sql_file}")
            except Exception as e:
                connection.rollback()
                print(f"Failed to apply: {sql_file}. Error: {e}")
                break

        print("Migrations complete.")
    except Exception as e:
        print(f"An error occurred while connecting to the database: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


if __name__ == "__main__":
    main()
