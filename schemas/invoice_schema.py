import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InvoiceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    invoice_number: str | None = Field(
        default=None,
        description="Invoice identifier exactly as shown; null if not present.",
    )
    invoice_date: str | None = Field(
        default=None,
        description="Invoice issue date as shown; null if not present.",
    )
    due_date: str | None = Field(
        default=None,
        description="Payment due date as shown; null if not present.",
    )
    vendor_name: str | None = Field(
        default=None,
        description="Name of the company or person issuing the invoice; null if absent.",
    )
    customer_name: str | None = Field(
        default=None,
        description="Name of the billed customer; null if absent.",
    )
    customer_email: str | None = Field(
        default=None,
        description="Customer email address exactly as shown; null if absent.",
    )
    subtotal_amount: float | None = Field(
        default=None,
        strict=False,
        allow_inf_nan=False,
        description="Invoice subtotal as a number, excluding separately stated tax; null if absent.",
    )
    tax_amount: float | None = Field(
        default=None,
        strict=False,
        allow_inf_nan=False,
        description="Tax amount as a number; null if absent.",
    )
    total_amount: float | None = Field(
        default=None,
        strict=False,
        allow_inf_nan=False,
        description="Invoice total as a number; null if absent.",
    )
    currency: str | None = Field(
        default=None,
        description="Currency code or symbol explicitly shown on the invoice; null if absent.",
    )
    payment_status: str | None = Field(
        default=None,
        description="Payment status explicitly stated on the invoice; null if absent.",
    )

    @field_validator(
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        mode="before",
    )
    @classmethod
    def validate_amount_is_numeric(cls, value: object) -> object:
        if value is not None and type(value) not in (int, float):
            raise ValueError("amounts must be JSON numbers")
        return value

    @field_validator("customer_email")
    @classmethod
    def validate_customer_email(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("customer_email must be a valid email address")
        return value
