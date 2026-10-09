from sandbox.database import get_connection, initialize_database


INVOICES = [
    {
        "vendor": "Acme Components",
        "invoice_number": "INV-1041",
        "amount": 12500.00,
        "currency": "INR",
        "invoice_date": "2026-09-15",
        "due_date": "2026-10-15",
        "status": "unpaid",
    },
    {
        "vendor": "Acme Components",
        "invoice_number": "INV-1042",
        "amount": 18450.00,
        "currency": "INR",
        "invoice_date": "2026-10-01",
        "due_date": "2026-10-31",
        "status": "unpaid",
    },
    {
        "vendor": "Acme Components",
        "invoice_number": "INV-1043",
        "amount": 22100.00,
        "currency": "INR",
        "invoice_date": "2026-09-25",
        "due_date": "2026-10-25",
        "status": "paid",
    },
    {
        "vendor": "Nova Systems",
        "invoice_number": "NOV-2081",
        "amount": 32000.00,
        "currency": "INR",
        "invoice_date": "2026-09-20",
        "due_date": "2026-10-20",
        "status": "unpaid",
    },
    {
        "vendor": "Vertex Technologies",
        "invoice_number": "VT-551",
        "amount": 15750.00,
        "currency": "INR",
        "invoice_date": "2026-10-02",
        "due_date": "2026-11-02",
        "status": "unpaid",
    },
]


def seed_database() -> None:

    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    for invoice in INVOICES:

        cursor.execute(
            """
            INSERT OR IGNORE INTO invoices (
                vendor,
                invoice_number,
                amount,
                currency,
                invoice_date,
                due_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice["vendor"],
                invoice["invoice_number"],
                invoice["amount"],
                invoice["currency"],
                invoice["invoice_date"],
                invoice["due_date"],
                invoice["status"],
            ),
        )

    connection.commit()
    connection.close()

    print(f"Seeded {len(INVOICES)} invoices.")


if __name__ == "__main__":
    seed_database()