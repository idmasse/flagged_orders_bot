import looker_sdk
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelnames)s] %(names)s: %(messages)s'
)

def looker_credentials():
    """init and return looker sdk instance"""
    try:
        sdk = looker_sdk.init40()
        logger.info('looker SDK initialized successfully')
        return sdk
    except Exception as e:
        logger.error(f'failed to initialize looker sdk: {e}')
        raise

def get_look_data(sdk, look_id):
    """fetch data from looker and return it as a list"""
    try:
        logger.info(f'fetching data from look id: {look_id}')
        result = sdk.run_look(look_id=look_id, result_format='json')
        data = json.loads(result)
        logger.info(f'fetched {len(data)} records from looker')
        return data
    except Exception as e:
        logger.error(f'error fetching data from looker api for look id: {look_id}')
        raise
