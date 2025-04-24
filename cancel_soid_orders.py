import logging
from api.flip_api import lookup_order, cancel_order
from utils.flip_auth import get_flip_access_token
from utils.looker_utils import looker_credentials, get_look_data
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

LOOK_ID = '851'

def fetch_and_cancel_soid_orders():
    logger.info("Starting process to fetch and cancel SOID orders from Looker and Flip API.")

    # Initialize Looker SDK and fetch data.
    sdk_instance = looker_credentials()
    look_data = get_look_data(sdk_instance, LOOK_ID)

    # Extract buyer order codes.
    buyer_order_codes = [entry.get("flip_orders_all.orderid") for entry in look_data]
    logger.info(f"Extracted {len(buyer_order_codes)} buyer order codes from Look data.")

    # Get Flip access token once.
    token = get_flip_access_token()
    if token:
        logger.info("Successfully obtained Flip access token.")
    else:
        logger.error("Failed to obtain Flip access token.")
        raise ValueError("Token could not be retrieved.")

    # Process each buyer order code.
    for code in buyer_order_codes:
        if not code:
            logger.warning("Encountered an empty or None buyer order code, skipping.")
            continue

        logger.info(f"Processing buyer order code: {code}")
        try:
            flip_order_id = lookup_order(code, token)
            if flip_order_id:
                logger.info(f"Found Flip Order ID '{flip_order_id}' for buyer order code '{code}'. Initiating cancellation...")
                cancel_order(flip_order_id, token)
            else:
                logger.warning(f"Lookup failed: No Flip Order ID found for buyer order code '{code}'.")
        except Exception as error:
            logger.error(f"Error processing buyer order code '{code}': {error}")

    logger.info("SOID order processing completed.")

if __name__ == "__main__":
    fetch_and_cancel_soid_orders()
