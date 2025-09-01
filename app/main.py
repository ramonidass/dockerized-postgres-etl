import logging
from settings import Settings
from api_client import AsyncAPIClient
from wallets_insights import get_wallet_activity


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():

    pass
