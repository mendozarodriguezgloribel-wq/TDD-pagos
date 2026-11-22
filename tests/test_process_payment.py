from decimal import Decimal

from source.payments.models import GatewayResponse, Payment, PaymentStatus
from source.payments.services import PaymentService

AMOUNT = Decimal("50.00")


class TestApprovedPayment:
    def test_approved_payment_is_saved_and_returned(self, service, gateway, repository):
        # Stub: simula que la pasarela externa aprueba el cobro
        gateway.charge.return_value = GatewayResponse(approved=True, transaction_id="txn_123")

        payment = service.process_payment("ORD-01", AMOUNT, "USD", "tok_visa")

        assert payment.status == PaymentStatus.APPROVED
        assert payment.transaction_id == "txn_123"

        # Mock: verifica las llamadas exactas a las dependencias externas
        gateway.charge.assert_called_once_with(AMOUNT, "USD", "tok_visa")
        repository.save.assert_called_once_with(payment)