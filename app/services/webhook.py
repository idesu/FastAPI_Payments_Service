import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookSender:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @retry(
        stop=stop_after_attempt(settings.WEBHOOK_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=settings.WEBHOOK_RETRY_BASE_DELAY,
            min=2,
            max=20,
        ),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def _send_webhook(self, url: str, payload: dict) -> None:
        response = await self.client.post(url, json=payload)
        response.raise_for_status()

    async def send_with_retries(self, url: str, payload: dict) -> bool:
        try:
            await self._send_webhook(url, payload)
            return True
        except Exception as e:
            logger.error(
                f"Webhook delivery failed after {settings.WEBHOOK_MAX_RETRIES} attempts: {e}"
            )
            return False

    async def close(self):
        await self.client.aclose()
