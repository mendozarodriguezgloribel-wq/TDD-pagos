from unittest.mock import create_autospec

import pytest

from source.payments.ports import PaymentGateway, PaymentRepository, ReceiptNotifier
from source.payments.services import PaymentService


@pytest.fixture
def gateway():
    # autospec: el doble respeta la firma del contrato y falla si se invoca mal
    return create_autospec(PaymentGateway, instance=True)


@pytest.fixture
def repository():
    repo = create_autospec(PaymentRepository, instance=True)
    repo.find_by_order_id.return_value = None  # Stub: no existe un pago previo
    return repo


@pytest.fixture
def notifier():
    return create_autospec(ReceiptNotifier, instance=True)


@pytest.fixture
def service(gateway, repository, notifier):
    return PaymentService(gateway, repository, notifier)