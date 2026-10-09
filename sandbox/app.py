from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException,Form, Query
from pydantic import BaseModel

from sandbox.database import get_connection, initialize_database


app = FastAPI(
    title="CentrAlign Simulated Company API",
    description="Simulated enterprise systems for the autonomous AI worker.",
    version="1.0.0",
)
templates = Jinja2Templates(
    directory="sandbox/templates"
)


# --------------------------------------------------
# Startup
# --------------------------------------------------

@app.on_event("startup")
def startup():
    initialize_database()


# --------------------------------------------------
# Models
# --------------------------------------------------

class APInvoiceCreate(BaseModel):
    invoice_number: str
    vendor: str
    amount: float
    currency: str = "INR"
    due_date: str


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "centr-align-simulated-company",
    }


# --------------------------------------------------
# Invoice APIs
# --------------------------------------------------

@app.get("/api/invoices")
def list_invoices(
    vendor: str | None = Query(default=None),
):
    connection = get_connection()

    if vendor:
        rows = connection.execute(
            """
            SELECT *
            FROM invoices
            WHERE LOWER(vendor) = LOWER(?)
            ORDER BY invoice_date DESC
            """,
            (vendor,),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM invoices
            ORDER BY invoice_date DESC
            """
        ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "invoices": [dict(row) for row in rows],
    }


@app.get("/api/invoices/{invoice_number}")
def get_invoice(invoice_number: str):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM invoices
        WHERE invoice_number = ?
        """,
        (invoice_number,),
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    return dict(row)


# --------------------------------------------------
# AP / ERP APIs
# --------------------------------------------------

@app.post("/api/ap/invoices")
def create_ap_invoice(invoice: APInvoiceCreate):

    connection = get_connection()

    # Prevent duplicate invoice creation.
    existing = connection.execute(
        """
        SELECT *
        FROM ap_records
        WHERE invoice_number = ?
        """,
        (invoice.invoice_number,),
    ).fetchone()

    if existing:
        connection.close()

        raise HTTPException(
            status_code=409,
            detail="Invoice already exists in AP",
        )

    created_at = datetime.now(timezone.utc).isoformat()

    cursor = connection.execute(
        """
        INSERT INTO ap_records (
            invoice_number,
            vendor,
            amount,
            currency,
            due_date,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice.invoice_number,
            invoice.vendor,
            invoice.amount,
            invoice.currency,
            invoice.due_date,
            "pending",
            created_at,
        ),
    )

    connection.commit()

    record_id = cursor.lastrowid

    row = connection.execute(
        """
        SELECT *
        FROM ap_records
        WHERE id = ?
        """,
        (record_id,),
    ).fetchone()

    connection.close()

    return {
        "message": "AP invoice created",
        "record": dict(row),
    }


@app.get("/api/ap/invoices")
def list_ap_invoices():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM ap_records
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return {
        "count": len(rows),
        "records": [dict(row) for row in rows],
    }


@app.get("/api/ap/invoices/{invoice_number}")
def get_ap_invoice(invoice_number: str):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM ap_records
        WHERE invoice_number = ?
        """,
        (invoice_number,),
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="AP record not found",
        )

    return dict(row)
# --------------------------------------------------
# Browser Invoice Portal
# --------------------------------------------------

@app.get("/invoices", response_class=HTMLResponse)
def invoice_portal(request: Request, vendor: str | None = None):
    connection = get_connection()

    if vendor:
        rows = connection.execute(
            """
            SELECT *
            FROM invoices
            WHERE vendor LIKE ?
            ORDER BY invoice_date DESC
            """,
            (f"%{vendor}%",),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT *
            FROM invoices
            ORDER BY invoice_date DESC
            """
        ).fetchall()

    connection.close()

    invoices = [dict(row) for row in rows]

    return templates.TemplateResponse(
        request=request,
        name="invoices.html",
        context={"invoices": invoices},
    )


@app.get("/invoices/{invoice_number}", response_class=HTMLResponse)
def invoice_detail(
    request: Request,
    invoice_number: str,
):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM invoices
        WHERE invoice_number = ?
        """,
        (invoice_number,),
    ).fetchone()

    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    invoice = dict(row)

    return templates.TemplateResponse(
        request=request,
        name="invoice_detail.html",
        context={"invoice": invoice},
    )
# --------------------------------------------------
# Browser AP / ERP
# --------------------------------------------------

@app.get("/ap", response_class=HTMLResponse)
def ap_portal(request: Request):

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM ap_records
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    records = [dict(row) for row in rows]

    return templates.TemplateResponse(
        request=request,
        name="ap.html",
        context={"records": records},
    )


@app.get("/ap/new", response_class=HTMLResponse)
def ap_new_form(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="ap_new.html",
        context={},
    )
@app.post("/ap/new", response_class=HTMLResponse)
def create_ap_invoice_from_browser(
    request: Request,
    invoice_number: str = Form(...),
    vendor: str = Form(...),
    amount: float = Form(...),
    currency: str = Form(...),
    due_date: str = Form(...),
):
    connection = get_connection()

    existing = connection.execute(
        """
        SELECT *
        FROM ap_records
        WHERE invoice_number = ?
        """,
        (invoice_number,),
    ).fetchone()

    if existing:
        connection.close()

        return templates.TemplateResponse(
            request=request,
            name="ap_new.html",
            context={
                "error": "Invoice already exists in AP.",
            },
            status_code=409,
        )

    created_at = datetime.now(timezone.utc).isoformat()

    cursor = connection.execute(
        """
        INSERT INTO ap_records (
            invoice_number,
            vendor,
            amount,
            currency,
            due_date,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            vendor,
            amount,
            currency,
            due_date,
            "pending",
            created_at,
        ),
    )

    connection.commit()

    record_id = cursor.lastrowid

    connection.close()

    return templates.TemplateResponse(
        request=request,
        name="ap_success.html",
        context={
            "invoice_number": invoice_number,
            "record_id": record_id,
        },
    )