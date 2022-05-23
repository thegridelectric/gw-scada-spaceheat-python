import re
import json
import datetime
import pytz
import math
import numpy as np
import subprocess
import socket
from contextlib import closing
import gw.property_format

from enums.recognized_currency_unit import RecognizedCurrencyUnit

snake_add_underscore_to_camel_pattern = re.compile(r'(?<!^)(?=[A-Z])')

def slot_start_s_from_market_slot_alias(market_slot_alias):
    if not gw.property_format.is_market_slot_alias_lrd_format(market_slot_alias):
        raise Exception(f"market slot alias {market_slot_alias} does not have market slot alias lrd format!")
    x = market_slot_alias.split('.')
    slot_start_utc_s = x[-1]
    return int(slot_start_utc_s)

def p_node_alias_from_market_alias(market_alias):
    if not gw.property_format.is_market_alias_lrd_format(market_alias):
        raise Exception(f"market alias {market_alias} does not have market alias lrd format!")
    x = market_alias.split('.')
    p_node_alias = ".".join(x[1:])
    return p_node_alias

def market_alias_fom_market_slot_alias(market_slot_alias):
    if not gw.property_format.is_market_slot_alias_lrd_format(market_slot_alias):
        raise Exception(f"market slot alias {market_slot_alias} does not have market slot alias lrd format!")
    x = market_slot_alias.split('.')  
    market_alias_lrd = ".".join(x[:-1])
    return market_alias_lrd

def p_node_alias_from_market_slot_alias(market_slot_alias):
    return p_node_alias_from_market_alias(market_alias_fom_market_slot_alias(market_slot_alias))

def camel_to_snake(name):
    return snake_add_underscore_to_camel_pattern.sub('_', name).lower()


def snake_to_camel(word):
    import re
    return ''.join(x.capitalize() or '_' for x in word.split('_'))


def string_to_dict(payload_as_string):
    payload_as_dict = json.loads(payload_as_string)
    return payload_as_dict

def log_style_utc_date(timestamp):
    d = datetime.datetime.utcfromtimestamp(timestamp)
    d = pytz.UTC.localize(d)
    utc_date = d.strftime("%Y-%m-%d %H:%M:%S")
    return utc_date + d.strftime(" %Z")

def log_style_utc_date_w_millis(timestamp):
    d = datetime.datetime.utcfromtimestamp(timestamp)
    d = pytz.UTC.localize(d)
    millis = round(d.microsecond / 1000)
    if millis == 1000:
        d += datetime.timedelta(seconds=1)
        millis = 0
    utc_date = d.strftime("%Y-%m-%d %H:%M:%S")
    if 0 <= millis < 10:
        millis_string = f".00{millis}"
    elif 10 <= millis < 100:
        millis_string = f".0{millis}"
    else:
        millis_string = f".{millis}"
    return utc_date + millis_string + d.strftime(" %Z")

def csv_george_1_style_utc_date_w_millis(timestamp):
    d = datetime.datetime.utcfromtimestamp(timestamp)
    d = pytz.UTC.localize(d)
    millis = round(d.microsecond / 1000)/1000
    utc_date = d.strftime("%Y-%m-%d %H:%M:%S")
    return utc_date + ".%d" % millis

def screen_style_utc_date_w_millis(timestamp):
    d = datetime.datetime.utcfromtimestamp(timestamp)
    d = pytz.UTC.localize(d)
    millis = round(d.microsecond / 1000)
    utc_date = d.strftime("%M:%S")
    if 0 <= millis < 10:
        millis_string = f".00{millis}"
    elif 10 <= millis < 100:
        millis_string = f".0{millis}"
    else:
        millis_string = f".{millis}"
    return utc_date + millis_string

def screen_style_utc_date_s(timestamp):
    d = datetime.datetime.utcfromtimestamp(timestamp)
    d = pytz.UTC.localize(d)
    utc_date = d.strftime("%Y-%m-%d %H:%M:%S")
    return utc_date + ' UTC'

def get_mp_alias(payload):
    if "MpAlias" not in payload.keys():
        raise Exception(f"payload {payload} sent without MpAlias!")
    else:
        return payload['MpAlias']


def enum_values(enum):
    return list(map(lambda x: x.value, enum))


def get_git_short_commit() -> str:
    return bytes.decode(subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])).split('\n')[0]

def socket_is_open(host, port) -> bool:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return True
        else:
            return False


def rld_alias(alias) -> str:
    words = alias.split('.')
    words = reversed(words)
    rld_alias = '.'.join(words)
    return rld_alias

def all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)

round_to_n = lambda x, n: x if x == 0 else round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


GBP_PER_USD = 1.32
def price_array_currency_conversion(from_currency: RecognizedCurrencyUnit, to_currency: RecognizedCurrencyUnit, prices: list):
        if from_currency == RecognizedCurrencyUnit.USD:
            from_multiplier = 1
        elif from_currency == RecognizedCurrencyUnit.GBP:
            from_multiplier = GBP_PER_USD
        else:
             raise Exception(f'Update conversion to handle {from_currency}!')
        
        if to_currency == RecognizedCurrencyUnit.USD:
            to_multiplier = 1
        elif to_currency == RecognizedCurrencyUnit.GBP:
            to_multiplier = GBP_PER_USD
        else:
             raise Exception(f'Update conversion to handle {to_currency}!')

        return to_multiplier/from_multiplier * np.array(prices)
 

def string_to_bool(value):
    if value == 'True' or value == 'TRUE':
        return True
    elif value == 'False' or value == 'FALSE':
        return False
    else:
        raise ValueError

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,RecognizedCurrencyUnit):
            return obj.value
        if isinstance(obj, np.int64):
            return int(obj)
        elif isinstance(obj, np.floating) or isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

