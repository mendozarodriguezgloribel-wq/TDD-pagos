from decimal import Decimal

from .models import GatewayResponse, Payment, PaymentStatus
from .ports import PaymentGateway, PaymentRepository, ReceiptNotifier


class PaymentService:
    """Orquesta el cobro de una orden sobre dependencias inyectadas."""

    def __init__(self, gateway: PaymentGateway, repository: PaymentRepository,
                notifier: ReceiptNotifier) -> None:
        self._gateway = gateway
        self._repository = repository
        self._notifier = notifier

    def process_payment(self, order_id: str, amount: Decimal,
                        currency: str, card_token: str) -> Payment:
        response = self._gateway.charge(amount, currency, card_token)
        payment = self._to_payment(order_id, amount, currency, response)
        self._repository.save(payment)
        if payment.status == PaymentStatus.APPROVED:
            self._notifier.send_receipt(payment)
        return payment

    @staticmethod
    def _to_payment(order_id: str, amount: Decimal, currency: str,
                    response: GatewayResponse) -> Payment:
        status = PaymentStatus.APPROVED if response.approved else PaymentStatus.DECLINED
        return Payment(order_id, amount, currency, status,
                    transaction_id=response.transaction_id, reason=response.reason)