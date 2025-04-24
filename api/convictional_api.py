import requests
import logging
import time
from dotenv import load_dotenv
import os

load_dotenv()

CONVICTIONAL_API_TOKEN=os.getenv('CONVICTIONAL_API_TOKEN')
CONVICTIONAL_API_BASE_URL=os.getenv('CONVICTIONAL_API_BASE_URL')
CONVICTIONAL_ORDERS_SEARCH_PATH=os.getenv('CONVICTIONAL_ORDERS_SEARCH_PATH')

def fetch_convictional_orders(start_date, end_date, flagged_filter):
    base_url = f'{CONVICTIONAL_API_BASE_URL}{CONVICTIONAL_ORDERS_SEARCH_PATH}'
    start_datetime = f'{start_date}T08:00:00.000Z'
    end_datetime = f'{end_date}T19:32:01.584Z'

    params = {
        'createdAt[after]': start_datetime,
        'createdAt[before]': end_datetime,
        'filters[flagged]': str(flagged_filter).lower()
    }
    logging.info(f'convictional api initial params: {params}')

    headers = {
        'Accept': "application/json",
        'Content-Type': "application/json",
        'Authorization': CONVICTIONAL_API_TOKEN
    }

    all_orders_data = []
    next_page_url = base_url
    page_num = 1
    has_more = True

    while has_more and next_page_url:
        try:
            current_params = params if page_num == 1 else None
            response = requests.get(next_page_url, headers=headers, params=current_params, timeout=30)
            response.raise_for_status()
        
            json_data = response.json()

            if 'error' in json_data and json_data['error']:
                break

            orders = json_data.get('data', {}).get('orders', [])
            if orders:
                all_orders_data.extend(orders)
                logging.info(f'fetched {len(orders)} from page {page_num}')
            else:
                logging.info(f'no orders found on page {page_num}')

            has_more = json_data.get('has_more', False)
            if has_more:
                next_page_url = json_data.get('next')
                if not next_page_url:
                    has_more = False
                page_num += 1
                time.sleep(0.5)
            else:
                next_page_url = None
                logging.info('no more pages found')

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error fetching Convictional orders: {e.response.status_code} - {e.response.text}")
            break # Stop fetching on HTTP error
        except requests.exceptions.RequestException as e:
            logging.error(f"Request Exception fetching Convictional orders: {e}")
            break # Stop fetching on connection error
        except ValueError: # Includes JSONDecodeError
            logging.error(f"Failed to decode JSON response from Convictional API. Status: {response.status_code}, Content: {response.text}")
            break
        except Exception as e:
            logging.error(f"An unexpected error occurred during Convictional fetch: {e}")
            break
    
    logging.info(f"Total Convictional orders fetched (Flagged={flagged_filter}): {len(all_orders_data)}")
    return all_orders_data