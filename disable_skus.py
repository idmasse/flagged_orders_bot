import pandas as pd
import logging
from utils.flip_auth import get_flip_access_token
from api.flip_api import disable_sku
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def read_flagged_orders(file_path):
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully read {file_path} with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return None

def disable_all_flagged_skus(file_path):
    token = get_flip_access_token()
    if not token:
        logger.error("Could not get access token. Exiting...")
        return

    df = read_flagged_orders(file_path)
    if df is None:
        return

    for _, row in df.iterrows():
        flagged_message = str(row['flagged_message']).strip().lower()
        buyer_item_codes = str(row['buyer_item_codes']).strip()

        #only process rows if flagged_message contains one of the required conditions
        if ("item is out of stock unexpectedly" in flagged_message or
            "cannot be a variant with components" in flagged_message):

            # extract SKUs from buyer_item_codes
            skus = [sku.strip() for sku in buyer_item_codes.split(';') if sku.strip()]
            for sku in skus:
                audit_status = "connectivity"
                # update audit_status if flagged_message contains correct error message
                if "cannot be a variant with components" in flagged_message:
                    audit_status = "unsupportedBundle"
                disable_sku(sku, audit_status, token)
        else:
            logger.info("Skipping row since flagged_message does not meet disable criteria.")

if __name__ == "__main__":
    disable_all_flagged_skus("flagged_orders.csv")
