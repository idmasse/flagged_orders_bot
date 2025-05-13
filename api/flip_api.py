import requests
import logging
import time
from utils.flip_auth import get_flip_access_token
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

FLIP_BASE_URL = os.getenv('FLIP_BASE_URL')
FLIP_DISABLE_SKUS_PATH = os.getenv('FLIP_DISABLE_SKUS_PATH')
FLIP_ORDERS_PATH = os.getenv('FLIP_ORDERS_PATH')
FLIP_CANCEL_ORDERS_PATH = '/shop/admin/orders/{order_id}/cancel/v1'
X_FLIPINATOR_TOOLS = os.getenv('X_FLIPINATOR_TOOLS')
MAX_RETRIES_FLIP = int(os.getenv('MAX_RETRIES_FLIP', 1))

def get_order_status_from_flip(order_id, limit=250):
    if not FLIP_BASE_URL or not FLIP_ORDERS_PATH:
        logging.error("Flip API URL or Path not configured")
        return None, None #return None for data and status code
    if not get_flip_access_token:
         logging.error("Flip access token function not available (import failed).")
         return None, None

    base_url = f"{FLIP_BASE_URL}{FLIP_ORDERS_PATH}"
    params = {'page': 1, 'limit': limit, 'customerOrderId': order_id}
    url = base_url # requests auto appends params from the dict
    last_status_code = None

    for attempt in range(MAX_RETRIES_FLIP + 1):
        access_token = get_flip_access_token()
        if not access_token:
            logging.error("Failed to get Flip access token. Cannot fetch order status.")
            return None, last_status_code

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "x-flipinator-tools": X_FLIPINATOR_TOOLS,
        }

        try:
            logging.debug(f"Attempt {attempt+1}: Calling Flip API: GET {url} with params {params}")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            last_status_code = response.status_code
            logging.debug(f"Flip API Response Status: {last_status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    logging.debug(f"Flip API Response Data: {data}")
                    return data, last_status_code
                except ValueError:
                    logging.error(f"Failed to decode JSON response from Flip API. Content: {response.text}")
                    return None, last_status_code

            elif response.status_code == 401:
                logging.warning(f"Received 401 Unauthorized from Flip API (Attempt {attempt + 1}/{MAX_RETRIES_FLIP + 1}).")
                if attempt < MAX_RETRIES_FLIP:
                    logging.info("Retrying after potential token refresh...")
                    time.sleep(1)
                    continue #retry the loop
                else:
                    logging.error("Max retries reached for Flip API after 401.")
                    break # exit loop

            else:
                logging.error(f"Flip API request failed with status {last_status_code}: {response.text}")
                break # exit loop for other errors

        except requests.exceptions.RequestException as e:
            logging.error(f"Error during Flip API request: {e}")
            last_status_code = getattr(e.response, 'status_code', None)
            if attempt < MAX_RETRIES_FLIP:
                logging.warning(f"Retrying Flip API call after error (Attempt {attempt + 1}/{MAX_RETRIES_FLIP + 1})...")
                time.sleep(2) #wait longer after connection errors
                continue
            else:
                 logging.error("Max retries reached for Flip API after connection error.")
                 break

    return None, last_status_code # return None if all retries fail

def disable_sku(sku, audit_status, token):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "x-flipinator-tools": X_FLIPINATOR_TOOLS
    }
    payload = {
        "skus": [sku],
        "auditStatus": audit_status
    }

    try:
        disable_skus_url = f'{FLIP_BASE_URL}{FLIP_DISABLE_SKUS_PATH}'
        response = requests.put(disable_skus_url, headers=headers, json=payload)
        response.raise_for_status()
        resp_data = response.json()
        logger.info(f"Disabled SKU {sku} with auditStatus '{audit_status}': {resp_data}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to disable SKU {sku}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response content: {e.response.text}")

def lookup_order(buyer_order_code, token):
    params = {"page": 1, "limit": 10, "customerOrderId": buyer_order_code}
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "x-flipinator-tools": X_FLIPINATOR_TOOLS
    }
    
    try:
        logger.info(f"Looking up order for buyer_order_code: {buyer_order_code}")
        flip_orders_url = f'{FLIP_BASE_URL}{FLIP_ORDERS_PATH}'
        response = requests.get(flip_orders_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        orders = data.get("data", [])
        
        if orders:
            order_id = orders[0].get("id")
            if order_id:
                logger.info(f"Found order id {order_id} for buyer_order_code {buyer_order_code}")
                return order_id
            else:
                logger.error(f"No order id found in the response for buyer_order_code {buyer_order_code}")
        else:
            logger.error(f"No orders returned for buyer_order_code {buyer_order_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error looking up order for {buyer_order_code}: {e}")
    return None

def cancel_order(order_id, token):
    flip_cancel_orders_url = f'{FLIP_BASE_URL}{FLIP_CANCEL_ORDERS_PATH}'
    url = flip_cancel_orders_url.format(order_id=order_id)
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "x-flipinator-tools": X_FLIPINATOR_TOOLS
    }
    payload = {
        "itemsBackToCart": False,
        "reasonForCancellation": "integrationFailure",
        "shouldCancelAdditionalOrders": False
    }
    
    try:
        logger.info(f"Attempting to cancel order id {order_id}")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        result = data.get("data", {}).get("result")
        if result == "success":
            logger.info(f"Successfully cancelled order {order_id}")
        else:
            logger.error(f"Cancellation failed for order {order_id}. Response: {data}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Status Code: {e.response.status_code} | Response: {e.response.text}")