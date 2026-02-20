from decimal import Decimal


PLAN_PRICES: dict[str, Decimal] = {
    "basic": Decimal("299.00"),
    "pro": Decimal("799.00"),
}

PLAN_PERIODS_DAYS: dict[str, int] = {
    "basic": 30,
    "pro": 90,
}
