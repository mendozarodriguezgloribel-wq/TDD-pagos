from decimal import Decimal

import pytest

from source.payments.exceptions import (
    GatewayUnavailableError,
    InvalidAmountError,
    PaymentProcessingError,
    UnsupportedCurrencyError,
)
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


class TestDeclinedPayment:
    def test_declined_payment_is_saved_without_receipt(
            self, service, gateway, repository, notifier):
        # Stub: la pasarela rechaza el cobro
        gateway.charge.return_value = GatewayResponse(approved=False, reason="insufficient_funds")

        payment = service.process_payment("ORD-02", AMOUNT, "USD", "tok_visa")

        assert payment.status == PaymentStatus.DECLINED
        assert payment.reason == "insufficient_funds"
        assert payment.transaction_id is None

        # Mock: el rechazo se guarda, pero no se envía recibo
        repository.save.assert_called_once_with(payment)
        notifier.send_receipt.assert_not_called()


class TestReceipt:
    def test_receipt_is_sent_once_when_payment_is_approved(self, service, gateway, notifier):
        gateway.charge.return_value = GatewayResponse(approved=True, transaction_id="txn_1")

        payment = service.process_payment("ORD-03", AMOUNT, "USD", "tok_visa")

        # Mock (spy de interacción): efecto secundario sin valor de retorno
        notifier.send_receipt.assert_called_once_with(payment)


class TestValidation:
    @pytest.mark.parametrize("invalid_amount", [Decimal("0"), Decimal("-5.00"), 50.0, "50"])
    def test_rejects_invalid_amount_without_calling_dependencies(
            self, service, gateway, repository, invalid_amount):
        with pytest.raises(InvalidAmountError):
            service.process_payment("ORD-04", invalid_amount, "USD", "tok_visa")

        gateway.charge.assert_not_called()
        repository.save.assert_not_called()

    @pytest.mark.parametrize("invalid_currency", ["XYZ", "usd"])
    def test_rejects_unsupported_currency(self, service, gateway, invalid_currency):
        with pytest.raises(UnsupportedCurrencyError):
            service.process_payment("ORD-04", AMOUNT, invalid_currency, "tok_visa")

        gateway.charge.assert_not_called()

    def test_accepts_currency_added_by_injection(self, gateway, repository, notifier):
        service = PaymentService(gateway, repository, notifier,
                                supported_currencies=frozenset({"USD", "GBP"}))
        gateway.charge.return_value = GatewayResponse(approved=True, transaction_id="txn_gbp")

        payment = service.process_payment("ORD-04", AMOUNT, "GBP", "tok_visa")

        assert payment.currency == "GBP"

class TestIdempotency:
    def test_returns_existing_approved_payment_without_charging_again(
            self, service, gateway, repository, notifier):
        existing = Payment("ORD-05", AMOUNT, "USD", PaymentStatus.APPROVED, "txn_old")
        # Stub: el repositorio ya tiene un pago aprobado para la orden
        repository.find_by_order_id.return_value = existing

        payment = service.process_payment("ORD-05", AMOUNT, "USD", "tok_visa")

        assert payment is existing
        repository.find_by_order_id.assert_called_once_with("ORD-05")
        gateway.charge.assert_not_called()
        repository.save.assert_not_called()
        notifier.send_receipt.assert_not_called()

    def test_charges_again_when_previous_payment_was_declined(
            self, service, gateway, repository):
        repository.find_by_order_id.return_value = Payment(
            "ORD-05", AMOUNT, "USD", PaymentStatus.DECLINED, reason="card_expired")
        gateway.charge.return_value = GatewayResponse(approved=True, transaction_id="txn_new")

        payment = service.process_payment("ORD-05", AMOUNT, "USD", "tok_new")

        assert payment.status == PaymentStatus.APPROVED
        gateway.charge.assert_called_once_with(AMOUNT, "USD", "tok_new")