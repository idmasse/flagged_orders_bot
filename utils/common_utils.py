import os
import csv
import logging
from datetime import datetime, timedelta

def get_today_date():
    """Returns today's date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")

def get_yesterday_date():
    """Returns yesterday's date in YYYY-MM-DD format."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def append_to_csv(filepath, data_rows, header):
    """Appends data rows to a CSV file. Writes header if file is new or empty."""
    if not data_rows:
        logging.debug(f"No data provided to write to {filepath}")
        return
    file_exists = os.path.exists(filepath)
    is_empty = not file_exists or os.path.getsize(filepath) == 0
    try:
        # Ensure the directory exists if filepath includes directories
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if is_empty:
                writer.writerow(header)
                logging.info(f"Writing header to new/empty file: {filepath}")
            writer.writerows(data_rows)
            logging.info(f"Appended {len(data_rows)} rows to {filepath}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {filepath}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during CSV writing: {e}")