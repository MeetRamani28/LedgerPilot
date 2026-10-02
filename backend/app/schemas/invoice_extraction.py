import math
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ExtractedLineItem(BaseModel):
    line_number: int = Field(default=1, description="Line number of item on invoice")
    description: str = Field(..., min_length=1, description="Description of good or service")
    quantity: float = Field(..., gt=0, description="Quantity billed")
    unit_price: float = Field(..., ge=0, description="Unit price per item")
    total_amount: float = Field(..., ge=0, description="Line item total amount")
    po_line_reference: Optional[str] = Field(default=None, description="PO item reference if present")

    @model_validator(mode="after")
    def validate_line_total(self) -> "ExtractedLineItem":
        calculated = round(self.quantity * self.unit_price, 2)
        reported = round(self.total_amount, 2)
        # Allow tolerance of up to 2 cents for rounding differences
        if not math.isclose(calculated, reported, abs_tol=0.02):
            raise ValueError(
                f"Line item math mismatch: {self.quantity} x {self.unit_price} = {calculated}, "
                f"but total is reported as {reported}"
            )
        return self


class ExtractedInvoice(BaseModel):
    invoice_number: str = Field(..., min_length=1, description="Unique invoice number")
    vendor_name: str = Field(..., min_length=1, description="Vendor name")
    vendor_tax_id: Optional[str] = Field(default=None, description="Vendor tax or VAT ID")
    vendor_address: Optional[str] = Field(default=None, description="Vendor billing address")
    invoice_date: Optional[str] = Field(default=None, description="Invoice date (YYYY-MM-DD or raw)")
    due_date: Optional[str] = Field(default=None, description="Payment due date")
    purchase_order_number: Optional[str] = Field(default=None, description="Purchase order reference number")
    currency: str = Field(default="USD", max_length=5, description="ISO currency code")
    line_items: list[ExtractedLineItem] = Field(..., min_length=1, description="List of line items")
    subtotal: float = Field(..., ge=0, description="Subtotal before tax")
    tax_amount: float = Field(default=0.0, ge=0, description="Tax or VAT amount")
    total_amount: float = Field(..., ge=0, description="Grand total amount")
    payment_terms: Optional[str] = Field(default=None, description="Payment terms like Net 30")

    @model_validator(mode="after")
    def validate_totals_arithmetic(self) -> "ExtractedInvoice":
        # 1. Verify sum of line items equals subtotal within $0.05
        line_sum = round(sum(item.total_amount for item in self.line_items), 2)
        reported_subtotal = round(self.subtotal, 2)
        if not math.isclose(line_sum, reported_subtotal, abs_tol=0.05):
            raise ValueError(
                f"Sum of line items ({line_sum}) does not match subtotal ({reported_subtotal})"
            )

        # 2. Verify subtotal + tax equals total_amount within $0.05
        calculated_total = round(reported_subtotal + self.tax_amount, 2)
        reported_total = round(self.total_amount, 2)
        if not math.isclose(calculated_total, reported_total, abs_tol=0.05):
            raise ValueError(
                f"Subtotal ({reported_subtotal}) + Tax ({self.tax_amount}) = {calculated_total}, "
                f"which does not match total amount ({reported_total})"
            )

        return self
