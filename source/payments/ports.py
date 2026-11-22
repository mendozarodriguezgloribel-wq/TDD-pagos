from decimal import Decimal
from typing import Optional, Protocol

from .models import GatewayResponse, Payment


class PaymentGateway(Protocol):
    """Contrato de la pasarela de pago externa (servicio de terceros)."""

    def charge(self, amount: Decimal, currency: str, card_token: str) -> GatewayResponse:
        """Solicita el cobro y devuelve la respuesta de la pasarela."""
        ...


class PaymentRepository(Protocol):
    """Contrato que simula la base de datos de pagos."""

    def save(self, payment: Payment) -> None:
        """Persiste el resultado de un pago."""
        ...

    def find_by_order_id(self, order_id: str) -> Optional[Payment]:
        """Obtiene el pago de una orden o None si no existe."""
        ...


class ReceiptNotifier(Protocol):
    """Contrato del servicio de envío de recibos (correo)."""

    def send_receipt(self, payment: Payment) -> None:
        """Envía el recibo de un pago aprobado."""
        ...