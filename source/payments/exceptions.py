class PaymentError(Exception):
    """Error base del dominio de pagos."""


class InvalidAmountError(PaymentError):
    """Se lanza cuando el monto no es un Decimal positivo."""


class UnsupportedCurrencyError(PaymentError):
    """Se lanza cuando la moneda no está soportada."""


class GatewayUnavailableError(PaymentError):
    """La pasarela falló por causas técnicas (timeout, error 5xx)."""


class PaymentProcessingError(PaymentError):
    """El servicio no pudo completar el procesamiento del pago."""