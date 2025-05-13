import pandas as pd
import logging
from api.flip_api import lookup_order, cancel_order
from utils.flip_auth import get_flip_access_token
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def process_and_cancel_orders_from_csv(csv_file):
    token = get_flip_access_token()
    if not token:
        logger.error("Failed to retrieve access token. Exiting.")
        return

    try:
        df = pd.read_csv(csv_file)
        logger.info(f"Read {len(df)} rows from {csv_file}")
    except Exception as e:
        logger.error(f"Failed to read {csv_file}: {e}")
        return

    for index, row in df.iterrows():
        flagged_message = str(row.get("flagged_message", "")).lower().strip()
        #only proceed if flagged_message contains one of the flagged messages
        if ("item is out of stock unexpectedly" not in flagged_message and
            "cannot be a variant with components" not in flagged_message):
            logger.info(f"Skipping cancellation for row {index} as flagged_message does not meet criteria.")
            continue

        buyer_order_code = str(row.get("buyer_order_code", "")).strip()
        if not buyer_order_code:
            logger.error(f"No buyer_order_code found in row {index}. Skipping...")
            continue

        order_id = lookup_order(buyer_order_code, token)
        if order_id:
            cancel_order(order_id, token)
        else:
            logger.error(f"Skipping cancellation because no order id was found for buyer_order_code: {buyer_order_code}")

if __name__ == "__main__":
    process_and_cancel_orders_from_csv("flagged_orders.csv")
