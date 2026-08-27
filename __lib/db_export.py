import sqlite3

import mysql.connector
import psycopg2
from apify import Actor


async def export_to_sqlite(data_items: list[dict]) -> None:
    """Export crawled data to local SQLite file using sqlite3."""
    if not data_items:
        await Actor.log.info("No items to export to SQLite.")
        return

    try:
        conn = sqlite3.connect("__data/result.sqlite")
        cursor = conn.cursor()

        # Drop and recreate table
        cursor.execute("DROP TABLE IF EXISTS books")
        cursor.execute("""
            CREATE TABLE books (
                url TEXT,
                title TEXT,
                price REAL,
                rating INTEGER,
                stock_quantity INTEGER,
                description TEXT
            )
        """)

        # Insert rows
        for item in data_items:
            cursor.execute(
                """
                INSERT INTO books (url, title, price, rating, stock_quantity, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    item.get("url"),
                    item.get("title"),
                    item.get("price"),
                    item.get("rating"),
                    item.get("stock_quantity"),
                    item.get("description"),
                ),
            )

        conn.commit()
        Actor.log.info(f"Exported {len(data_items)} rows to SQLite: data/result.sqlite")
    except Exception as e:
        Actor.log.error(f"SQLite export failed: {str(e)}")
    finally:
        if "conn" in locals():
            conn.close()


async def export_to_mysql(data_items: list[dict], mysql_config: dict) -> None:
    """Export crawled data to MySQL using mysql.connector."""
    if not data_items or not mysql_config:
        Actor.log.info("Skipping MySQL export (no config or no data).")
        return

    try:
        conn = mysql.connector.connect(
            host=mysql_config.get("host", "localhost"),
            port=mysql_config.get("port", 3306),
            user=mysql_config["user"],
            password=mysql_config.get("password", ""),
            database=mysql_config["database"],
        )

        if conn.is_connected():
            cursor = conn.cursor()
            table_name = mysql_config.get("table", "books")

            # Drop and recreate table
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute(f"""
                CREATE TABLE {table_name} (
                    url TEXT,
                    title TEXT,
                    price FLOAT,
                    rating INT,
                    stock_quantity INT,
                    description TEXT
                )
            """)

            # Insert rows
            for item in data_items:
                cursor.execute(
                    f"""
                    INSERT INTO {table_name} (url, title, price, rating, stock_quantity, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """,
                    (
                        item.get("url"),
                        item.get("title"),
                        item.get("price"),
                        item.get("rating"),
                        item.get("stock_quantity"),
                        item.get("description"),
                    ),
                )

            conn.commit()
            Actor.log.info(
                f"Exported {len(data_items)} rows to MySQL table '{table_name}'"
            )
    except Exception as e:
        Actor.log.error(f"MySQL export failed: {str(e)}")
    finally:
        if "conn" in locals() and conn.is_connected():
            conn.close()


async def export_to_postgresql(data_items: list[dict], postgres_config: dict) -> None:
    """Export crawled data to PostgreSQL using psycopg2."""
    if not data_items or not postgres_config:
        Actor.log.info("Skipping PostgreSQL export (no config or no data).")
        return

    try:
        conn = psycopg2.connect(
            host=postgres_config.get("host", "localhost"),
            port=postgres_config.get("port", 5432),
            user=postgres_config["user"],
            password=postgres_config.get("password", ""),
            database=postgres_config["database"],
        )

        cursor = conn.cursor()
        table_name = postgres_config.get("table", "books")

        # Drop and recreate table
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                url TEXT,
                title TEXT,
                price FLOAT,
                rating INTEGER,
                stock_quantity INTEGER,
                description TEXT
            )
        """)

        # Insert rows
        for item in data_items:
            cursor.execute(
                f"""
                INSERT INTO {table_name} (url, title, price, rating, stock_quantity, description)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
                (
                    item.get("url"),
                    item.get("title"),
                    item.get("price"),
                    item.get("rating"),
                    item.get("stock_quantity"),
                    item.get("description"),
                ),
            )

        conn.commit()
        Actor.log.info(
            f"Exported {len(data_items)} rows to PostgreSQL table '{table_name}'"
        )
    except Exception as e:
        Actor.log.error(f"PostgreSQL export failed: {str(e)}")
    finally:
        if "conn" in locals():
            conn.close()
