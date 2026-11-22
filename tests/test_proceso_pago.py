from decimal import Decimal
from unittest.mock import Mock

from source.payments.models import GatewayResponse, PaymentStatus
from source.payments.services import PaymentService


class TestApprovedPayment:
    def test_approved_payment_is_saved_and_returned(self):
        # Stub: simula que la pasarela externa aprueba el cobro
        gateway = Mock()
        gateway.charge.return_value = GatewayResponse(approved=True, transaction_id="txn_123")
        repository = Mock()
        notifier = Mock()

        service = PaymentService(gateway=gateway, repository=repository, notifier=notifier)
        payment = service.process_payment("ORD-01", Decimal("50.00"), "USD", "tok_visa")

        assert payment.status == PaymentStatus.APPROVED
        assert payment.transaction_id == "txn_123"

        # Mock: verifica las llamadas exactas a las dependencias externas
        gateway.charge.assert_called_once_with(Decimal("50.00"), "USD", "tok_visa")
        repository.save.assert_called_once_with(payment)