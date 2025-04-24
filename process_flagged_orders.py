from utils.common_utils import get_today_date, get_yesterday_date
from api.convictional_api import fetch_convictional_orders
from api.flip_api import get_order_status_from_flip
import logging
import csv
import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_FLIP_STATE = os.getenv('ALLOWED_FLIP_STATE')
FLAGGED_ORDERS_CSV = 'flagged_orders.csv'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')

def write_to_csv(filepath, data_rows, header):
    """Overwrites CSV file with new data, not keeping historical entries."""
    if not data_rows:
        logging.debug(f"No data provided to write to {filepath}")
        return
    
    try:
        # Only attempt to make directories if there is a directory part in the filepath
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            logging.info(f"Writing header to file: {filepath}")
            writer.writerows(data_rows)
            logging.info(f"Wrote {len(data_rows)} rows to {filepath}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {filepath}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during CSV writing: {e}")

def fetch_and_process_flagged_orders():
    """Fetches flagged orders, gets Flip status, filters, and saves to CSV."""
    logging.info("--- Starting processing of FLAGGED orders ---")
    # Determine date range
    start_date = get_yesterday_date()
    end_date = get_today_date()
    logging.info(f"Using date range: {start_date} to {end_date}")

    # Fetch flagged orders from Convictional
    convictional_orders = fetch_convictional_orders(start_date, end_date, flagged_filter=True)
    if not convictional_orders:
        logging.info("No flagged orders fetched from Convictional for this date range.")
        logging.info("--- Finished processing FLAGGED orders ---")
        return

    processed_orders = []
    header = ["convictional_order_id", "flagged_message", "buyer_order_code", "flip_order_state", "buyer_item_codes"]

    for order in convictional_orders:
        conv_order_id = order.get("_id")
        buyer_order_code = order.get("buyerOrderCode")
        flagged_message = order.get("flaggedMessage", "")
        items = order.get("items", [])
        buyer_item_codes = "; ".join([item.get("buyerItemCode", "") for item in items if item.get("buyerItemCode")])

        if not buyer_order_code:
            logging.warning(f"Skipping Convictional Order {conv_order_id}: Missing 'buyerOrderCode'.")
            continue

        logging.info(f"Getting Flip status for Convictional Order {conv_order_id} (Buyer Code: {buyer_order_code})...")
        flip_data, status_code = get_order_status_from_flip(buyer_order_code)

        # Process based on Flip API result
        flip_order_state = "Error or Not Found"  # Default status
        if flip_data and flip_data.get("data"):
            if flip_data["data"]:
                flip_order_state = flip_data["data"][0].get("state", "State Not Found")
            else:
                logging.warning(f"Flip API returned data for {buyer_order_code}, but the 'data' list is empty.")
                flip_order_state = "Flip Data Empty"
        elif status_code:
            logging.warning(f"Failed to get Flip data for {buyer_order_code}. Flip API Status: {status_code}")
            flip_order_state = f"Flip API Error ({status_code})"
        else:
            logging.warning(f"Failed to get Flip data for {buyer_order_code} (No specific status code returned).")

        # Filter based on the Flip order state
        if flip_order_state == ALLOWED_FLIP_STATE:
            processed_orders.append([
                conv_order_id,
                flagged_message,
                buyer_order_code,
                flip_order_state,
                buyer_item_codes
            ])
            logging.info(f"Order {conv_order_id} matched state '{ALLOWED_FLIP_STATE}' and will be saved.")
        else:
            logging.info(f"Order {conv_order_id} skipped. Flip state '{flip_order_state}' != '{ALLOWED_FLIP_STATE}'.")

    # Write valid orders to CSV (overwriting previous content)
    if processed_orders:
        write_to_csv(FLAGGED_ORDERS_CSV, processed_orders, header)
    else:
        logging.info("No flagged orders met the required Flip state criteria.")
        if os.path.exists(FLAGGED_ORDERS_CSV):
            write_to_csv(FLAGGED_ORDERS_CSV, [], header)
            logging.info(f"Cleared existing data in {FLAGGED_ORDERS_CSV}")
    logging.info("--- Finished processing FLAGGED orders ---")

if __name__ == "__main__":
    fetch_and_process_flagged_orders()

