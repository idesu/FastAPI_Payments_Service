import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebhookSender:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)

    async def send_with_retries(self, url: str, payload: dict) -> bool:
        @retry(
            stop=stop_after_attempt(settings.WEBHOOK_MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=2, max=20),
            reraise=True,
        )
        async def _send():
            async with self.client as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

        await _send()
