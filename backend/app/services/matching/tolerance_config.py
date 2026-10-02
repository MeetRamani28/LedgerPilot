from pydantic import BaseModel, Field


class ToleranceConfig(BaseModel):
    # Percentage tolerance for unit price (e.g. 0.02 = 2%)
    price_tolerance_pct: float = Field(default=0.02, ge=0.0, le=1.0)
    
    # Percentage tolerance for quantity overages (default 0% = strict)
    quantity_tolerance_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Absolute dollar tolerance for invoice total rounding
    total_tolerance_abs: float = Field(default=1.0, ge=0.0)
    
    # Maximum plausible tax rate (25%) before flagging anomaly
    tax_rate_max_pct: float = Field(default=0.25, ge=0.0, le=1.0)
    
    # Large transaction threshold for round-number fraud checks
    round_number_threshold: float = Field(default=10000.0, ge=0.0)
