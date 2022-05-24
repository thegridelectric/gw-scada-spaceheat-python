import re
import os
from dotenv import load_dotenv


snake_add_underscore_to_camel_pattern = re.compile(r'(?<!^)(?=[A-Z])')

def camel_to_snake(name):
    return snake_add_underscore_to_camel_pattern.sub('_', name).lower()

def get_secret(key):
    load_dotenv()
    value = os.getenv(key)
    if  value is None:
        raise Exception(f"Missing {key} value in gw-scada-spaceheat-python/.env file!")
    elif value == 'None':
        return None
    return value