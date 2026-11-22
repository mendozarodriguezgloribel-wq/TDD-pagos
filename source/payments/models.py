from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


@dataclass(frozen=True)
class GatewayResponse:
    """Respuesta de la pasarela de pago externa."""
    approved: bool
    transaction_id: Optional[str] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class Payment:
    """Resultado inmutable del procesamiento de un pago."""
    order_id: str
    amount: Decimal
    currency: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    reason: Optional[str] = None
    @property
    def is_approved(self) -> bool:
        return self.status == PaymentStatus.APPROVED