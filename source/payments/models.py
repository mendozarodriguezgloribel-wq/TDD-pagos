from enum import Enum


class PaymentStatus(str, Enum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


class GatewayResponse:
    def __init__(self, approved: bool, transaction_id=None, reason=None):
        self.approved = approved
        self.transaction_id = transaction_id
        self.reason = reason


class Payment:
    def __init__(self, order_id, amount, currency, status,
            transaction_id=None, reason=None):
        self.order_id = order_id
        self.amount = amount
        self.currency = currency
        self.status = status
        self.transaction_id = transaction_id
        self.reason = reason