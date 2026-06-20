class PaymentProcessorError(Exception):
    """Базовое исключение для всех ошибок сервиса."""
    pass


class PaymentNotFound(PaymentProcessorError):
    """Платеж с указанным ID не найден."""
    pass


class IdempotencyConflict(PaymentProcessorError):
    """
    Исключение, выбрасываемое при попытке создать платеж с уже использованным
    idempotency key, если семантика API потребует ошибки.
    Сейчас мы не выбрасываем его, а возвращаем существующий платеж,
    что соответствует идемпотентности (повторный запрос возвращает тот же результат).
    """
    pass


class WebhookDeliveryError(PaymentProcessorError):
    """Ошибка доставки webhook после всех повторных попыток."""
    pass


class OutboxPublishError(PaymentProcessorError):
    """Ошибка публикации события из outbox."""
    pass