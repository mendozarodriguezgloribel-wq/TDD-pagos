import logging
from decimal import Decimal
from typing import FrozenSet, Optional

from .exceptions import (
    GatewayUnavailableError,
    InvalidAmountError,
    PaymentProcessingError,
    UnsupportedCurrencyError,
)
from .models import GatewayResponse, Payment, PaymentStatus
from .ports import PaymentGateway, PaymentRepository, ReceiptNotifier

logger = logging.getLogger(__name__)

DEFAULT_CURRENCIES: FrozenSet[str] = frozenset({"USD", "EUR", "DOP"})


class PaymentService:
    """Orquesta el cobro de una orden sobre dependencias inyectadas."""

    def __init__(self, gateway: PaymentGateway, repository: PaymentRepository,
                notifier: ReceiptNotifier,
                supported_currencies: FrozenSet[str] = DEFAULT_CURRENCIES,
                max_retries: int = 2) -> None:
        if max_retries < 0:
            raise ValueError("max_retries no puede ser negativo.")
        self._gateway = gateway
        self._repository = repository
        self._notifier = notifier
        self._supported_currencies = supported_currencies
        self._max_retries = max_retries

    def process_payment(self, order_id: str, amount: Decimal,
                        currency: str, card_token: str) -> Payment:
        self._validate(amount, currency)

        already_paid = self._find_approved(order_id)
        if already_paid:
            return already_paid

        response = self._charge(amount, currency, card_token)
        payment = self._to_payment(order_id, amount, currency, response)
        self._persist(payment)
        if payment.is_approved:
            self._send_receipt(payment)
        return payment

    def _validate(self, amount: Decimal, currency: str) -> None:
        # Decimal evita errores de redondeo; float y str se rechazan explícitamente
        if not isinstance(amount, Decimal) or amount <= 0:
            raise InvalidAmountError("El monto debe ser un Decimal mayor que cero.")
        if currency not in self._supported_currencies:
            raise UnsupportedCurrencyError(f"Moneda no soportada: {currency}.")

    def _find_approved(self, order_id: str) -> Optional[Payment]:
        existing = self._repository.find_by_order_id(order_id)
        return existing if existing and existing.is_approved else None

    def _charge(self, amount: Decimal, currency: str, card_token: str) -> GatewayResponse:
        attempts = self._max_retries + 1
        last_error: Optional[GatewayUnavailableError] = None
        for _ in range(attempts):
            try:
                return self._gateway.charge(amount, currency, card_token)
            except GatewayUnavailableError as exc:
                last_error = exc
        raise PaymentProcessingError(
            f"Pasarela no disponible tras {attempts} intentos.") from last_error

    def _persist(self, payment: Payment) -> None:
        try:
            self._repository.save(payment)
        except Exception as exc:
            raise PaymentProcessingError("Error al guardar el pago.") from exc

    def _send_receipt(self, payment: Payment) -> None:
        try:
            self._notifier.send_receipt(payment)
        except Exception:
            # El cobro ya se realizó y se guardó: un fallo de correo no lo revierte
            logger.warning("No se pudo enviar el recibo de la orden %s.",
                        payment.order_id, exc_info=True)

    @staticmethod
    def _to_payment(order_id: str, amount: Decimal, currency: str,
                    response: GatewayResponse) -> Payment:
        status =PaymentStatus.APPROVED if response.approved else PaymentStatus.DECLINED
        return Payment(order_id, amount, currency, status,
                    transaction_id=response.transaction_id, reason=response.reason)