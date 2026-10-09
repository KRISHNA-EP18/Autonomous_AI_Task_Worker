import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).parent / "company.db"


def get_connection() -> sqlite3.Connection:
    """
    Create a connection to the company SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database() -> None:
    """
    Create all required database tables.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # ------------------------------------------
    # Invoices received from vendors
    # ------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor TEXT NOT NULL,
            invoice_number TEXT NOT NULL UNIQUE,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'INR',
            invoice_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid'
        )
        """
    )

    # ------------------------------------------
    # Invoices entered into the AP system
    # ------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ap_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            vendor TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'INR',
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at: {DATABASE_PATH}")