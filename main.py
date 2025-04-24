import logging
from process_flagged_orders import fetch_and_process_flagged_orders
from disable_skus import disable_all_flagged_skus
from cancel_flagged_orders import process_and_cancel_orders_from_csv
from cancel_soid_orders import fetch_and_cancel_soid_orders

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FLAGGED_ORDERS_CSV = "flagged_orders.csv"

def main():
    logging.info("=== Starting order and sku disablement pipeline ===")
    
    # 1. Process flagged orders from Convictional and save to CSV
    logging.info("Step 1: Fetch and check flagged orders from Convictional.")
    fetch_and_process_flagged_orders()
    
    # 2. Disable SKUs for flagged orders
    logging.info("Step 2: Disabling SKUs based on flagged order message")
    disable_all_flagged_skus(FLAGGED_ORDERS_CSV)
    
    # 3. Lookup orders in Flip and cancel them
    logging.info("Step 3: Cancelling orders based on flagged orders message")
    process_and_cancel_orders_from_csv(FLAGGED_ORDERS_CSV)

    # Step 4: Lookup and cancel missing SOID orders
    logging.info("Step 4: Cancelling orders missing seller order ID")
    fetch_and_cancel_soid_orders()
    
    logging.info("=== Full processing pipeline completed. ===")

if __name__ == "__main__":
    main()
