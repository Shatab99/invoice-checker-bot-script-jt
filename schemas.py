from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date

class InvoiceLineItem(BaseModel):
    description: str = Field(..., description="Description of the item or service. Cannot be empty.")
    quantity: Optional[int] = Field(None, description="Quantity of the item, if specified. Must be an integer.")
    unit: str = Field(..., description="Unit of measurement (e.g., 'pcs', 'lot', '式'). Cannot be empty.")
    unit_price: Optional[int] = Field(None, description="Price per unit in JPY, if specified. Must be an integer.")
    amount: int = Field(..., description="Total amount for this line item in JPY. Must be an integer.")
    tax_code: str = Field(..., description="Tax code for this item. Must strictly be 'T10' (10%) or 'T08' (8%).")

class InvoicePayload(BaseModel):
    partner_code: str = Field(..., description="The partner code (e.g., 'P-1001') matching the supplier master list.")
    invoice_number: str = Field(..., description="The unique invoice number. Cannot be empty.")
    issue_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Issue date strictly in YYYY-MM-DD format.")
    due_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Due date strictly in YYYY-MM-DD format.")
    currency: str = Field("JPY", description="Currency code, must strictly be 'JPY'.")
    lines: List[InvoiceLineItem] = Field(..., min_length=1, description="List of line items on the invoice. Must contain at least one.")
    subtotal: int = Field(..., description="Total amount before tax. Must be an integer.")
    tax_amount: int = Field(..., description="Total consumption tax amount. Must be an integer.")
    total_amount: int = Field(..., description="Total amount including tax. Must be an integer.")

    @field_validator('due_date')
    def validate_dates(cls, v, info):
        """Ensures the due_date is not earlier than the issue_date."""
        issue_date_str = info.data.get('issue_date')
        if issue_date_str and v:
            try:
                if date.fromisoformat(v) < date.fromisoformat(issue_date_str):
                    raise ValueError("due_date cannot be earlier than issue_date")
            except ValueError:
                pass 
        return v