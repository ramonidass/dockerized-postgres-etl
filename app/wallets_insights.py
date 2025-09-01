import logging
from typing import Dict
import httpx
from api_client import AsyncAPIClient
from settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def get_wallet_activity(
    api_client: AsyncAPIClient, wallet_id: str
) -> Dict[str, any]:
    try:
        response = api_client.get(settings.w_activity_endpoint)
        return response if isinstance(response, dict) else {}
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to fetch user {wallet_id}: {e}")
        return {}
    except httpx.RequestError as e:
        logger.error(f"Network error for user {wallet_id}: {e}")
    return {}
