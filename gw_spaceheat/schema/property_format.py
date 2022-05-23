import pytz
import pendulum
import struct
from data_classes.market_type_static import PlatformMarketType
from data_classes.price_method_static import PlatformPriceMethod
from enums.g_node_role import GNodeRole
from enums.g_node_status import GNodeStatus
from enums.market_type import MarketType
from enums.pr_cmd import PrCmd
from enums.price_source import PriceSource
from enums.recognized_currency_unit import RecognizedCurrencyUnit
from enums.recognized_irradiance_type import RecognizedIrradianceType
from enums.recognized_p_node_alias import RecognizedPNodeAlias
from enums.recognized_temperature_unit import RecognizedTemperatureUnit
from enums.simple_ctn_operating_mode import SimpleCtnOperatingMode
from enums.simple_dc_diesel_operating_mode_1_0 import \
    SimpleDcDieselOperatingMode_1_0
from enums.ta_operating_char_framework import TaOperatingCharFramework
from enums.tc_message_type_1_0_0 import TcMessageType_1_0_0
from enums.time_toggle import TimeToggle
from enums.weather_method import WeatherMethod
from enums.weather_source import WeatherSource
from enums.bid_offer_price_unit import BidOfferPriceUnit
from enums.bid_offer_quantity_unit import BidOfferQuantityUnit


def is_short_integer(candidate):
    try:
        struct.pack("h",candidate)
    except:
        print("short format requires (-32767 -1) <= number <= 32767")
        return False
    return True

def is_bid_offer_price_unit(candidate):
    try:
        BidOfferPriceUnit(candidate)
    except ValueError:
        return False
    return True

def is_bid_offer_quantity_unit(candidate):
    try:
        BidOfferQuantityUnit(candidate)
    except ValueError:
        return False
    return True

def is_world_instance_alias_format(candidate_alias):
    """AlphanumericString + '__' + Integer"""
    x = candidate_alias.split('__')
    if len(x) != 2:
        return False
    world_root_alias = x[0]
    idx = x[1]
    if not world_root_alias.isalnum():
        return False
    idx_as_float = float(idx)
    if idx_as_float != int(idx_as_float):
        return False
    return True


def is_g_node_lrd_alias_format(candidate):
    """AlphanumericStrings separated by periods, with most
    significant word to the left.  I.e. `dw1.ne` is the child of `dw1`. """
    try:
        x = candidate.split('.')
    except AttributeError:
        return False
    for word in x:
        if not word.isalnum():
            return False
    return True


def is_uuid_canonical_textual(candidate):
    try:
        x = candidate.split('-')
    except AttributeError:
        return False
    if len(x) != 5:
        return False
    for hex_word in x:
        try:
            y = int(hex_word, 16)
        except ValueError:
            return False
    if len(x[0]) != 8:
        return False
    if len(x[1]) != 4:
        return False
    if len(x[2]) != 4:
        return False
    if len(x[3]) != 4:
        return False
    if len(x[4]) != 12:
        return False
    return True


def is_non_negative_int64(candidate):
    if not isinstance(candidate, int):
        return False
    if candidate < 0:
        return False
    return True


def is_ta_operating_char_framework(candidate):
    try:
        TaOperatingCharFramework(candidate)
    except ValueError:
        return False
    return True


def is_simple_ctn_operating_mode(candidate):
    try:
        SimpleCtnOperatingMode(candidate)
    except ValueError:
        return False
    return True


def is_simple_dc_diesel_operating_mode_1_0(candidate):
    try:
        SimpleDcDieselOperatingMode_1_0(candidate)
    except ValueError:
        return False
    return True

def is_pr_cmd(candidate):
    try:
        PrCmd(candidate)
    except ValueError:
        return False
    return True

def is_time_toggle(candidate):
    try:
        TimeToggle(candidate)
    except ValueError:
        return False
    return True

def is_tc_message_type_1_0_0(candidate):
    try:
        TcMessageType_1_0_0(candidate)
    except ValueError:
        return False
    return True


def is_log_style_utc_date_w_millis(candidate):
    """ Example: '2020-11-17 14:57:00.525 UTC' """
    try:
        x = candidate.split(' ')
    except AttributeError:
        return False
    if x[2] != 'UTC':
        return False
    t_w_millis = x[1].split('.')
    if len(t_w_millis[1]) != 3:
        return False
    try:
        int(t_w_millis[1])
    except ValueError:
        return False
    hh, mm, ss = t_w_millis[0].split(':')
    try:
        hh = int(hh)
        mm = int(mm)
        ss = int(ss)
    except ValueError:
        return False
    if hh < 0 or hh > 23:
        return False
    if mm < 0 or mm > 59:
        return False
    if ss < 0 or ss  > 59:
        return False
    return True
    yyyy, MM, dd = x[0].split('-')
    if len(yyyy) != 4:
        return False
    try:
        yyyy = int(yyyy)
        MM = int(MM)
        dd = int(dd)
    except ValueError:
        return False
    if MM < 1 or MM > 12:
        return False
    if dd < 1 or dd > 31:
        return False


def is_gw_float(candidate):
    if isinstance(candidate, float):
        return True
    return False


def is_list_of_uuids(candidate):
    if not isinstance(candidate, list):
        return False
    for x in candidate:
        if not is_uuid_canonical_textual(x):
            return False
    return True


def is_admin_electrical_connection_request_1_0_0(candidate):
    if candidate == 'Connect' or candidate == 'Disconnect':
        return True
    return False


def is_float_fraction(candidate):
    if not isinstance(candidate, float):
        return False
    if candidate < 0:
        return False
    if candidate > 1:
        return False
    return True


def is_recognized_currency_unit(candidate):
    try:
        RecognizedCurrencyUnit(candidate)
    except ValueError:
        return False
    return True


def is_recognized_temperature_unit(candidate):
    try:
        RecognizedTemperatureUnit(candidate)
    except ValueError:
        return False
    return True


def is_recognized_irradiance_type(candidate):
    try:
        RecognizedIrradianceType(candidate)
    except ValueError:
        return False
    return True

def is_recognized_market_type(candidate):
    try:
        MarketType(candidate)
    except ValueError:
        return False
    return True

def is_recognized_market_type_alias(candidate):
    if candidate not in PlatformMarketType.keys():
        return False
    return True

def is_recognized_p_node_alias(candidate):
    c = ".".join(["w"] + candidate.split(".")[1:])
    try:
        RecognizedPNodeAlias(c)
    except ValueError:
        return False
    return True

def is_price_source(candidate):
    try:
        PriceSource(candidate)
    except ValueError:
        return False
    return True

def is_recognized_price_method(candidate):
    if candidate not in PlatformPriceMethod.keys():
        return False
    return True


def is_weather_source(candidate):
    try:
        WeatherSource(candidate)
    except ValueError:
        return False
    return True

def is_weather_method(candidate):
    try:
        WeatherMethod(candidate)
    except ValueError:
        return False
    return True


def is_recognized_bool_string(candidate):
    if candidate == 'True' or candidate == 'TRUE' or candidate == 'False' or candidate == 'FALSE':
         return True
    else:
        return False

def is_valid_month_hour_int_array(candidate):
    if type(candidate) != list:
        return False
    if len(candidate) != 12:
        return False
    for i in range(len(candidate)):
        month_list = candidate[i]
        if type(month_list) != list:
            return False
        if len(month_list) != 24:
            return False
        for j in range(len(month_list)):
            hour_value = month_list[j]
            if type(hour_value) != int:
                return False
        
def is_recognized_timezone_string(candidate):
    try:
        pytz.timezone(candidate)
    except:
        return False
    return True

def is_recognized_iso8601_utc(candidate):
    try:
        pendulum.parse(candidate)
    except:
        return False
    try:
        date, time_w_utc = candidate.split("T")
    except:
        return False
    try:
        year, month, day = date.split('-')
    except:
        return False
    if len(year) != 4:
        return False
    try:
        int(year)
    except:
        return False
    if time_w_utc[-1] != 'Z':
        return False
    time = time_w_utc[:-1]
    hour, minute,  second = time.split(':')
    two_digit_int_strings = [month, day, hour, minute, second]
    for s in two_digit_int_strings:
        if len(s) != 2:
            return False
        try:
            int(s)
        except:
            return False
    return True

def is_recognized_g_node_role_alias(candidate):
    try:
        GNodeRole(candidate)
    except ValueError:
        return False
    return True


def is_tuple_of_integer_pairs(candidate):
    #TODO: add this validation
    return True


def is_g_node_alias_to_idx_dict(candidate):
    #TODO: add this validation
    return True

def is_supervisor_container_type(candidate):
    #TODO: add
    return True

def is_recognized_supervisor_container_status(candidate):
    #TODO: add
    return True

def is_recognized_component_type(candidate):
    #TODO: add
    return True

def is_recognized_component_manufacturer(candidate):
    #TODO: add
    return True

def is_recognized_gni_status(canididate):
    #TODO: add
    return True

def is_recognized_grc_status(candidate):
    #TODO: add
    return True

def is_internet_date_time_milli_seconds_utc(candidate):
    #TODO: add
    return True

def is_tuple_of_two_uuids(candidate):
    try:
        elt0 = candidate[0]
    except:
        return False
    if not is_uuid_canonical_textual(elt0):
        return False
    try:
        elt1 = candidate[1]
    except:
        return False
    if not is_uuid_canonical_textual(elt1):
        return False
    if len(candidate) > 2:
        return False
    return True

def is_grid_run_class_alias_format(candidate):
    "Headscratcher for now"
    return True

def is_mod256(candidate):
    if not isinstance(candidate,int):
        return False
    if candidate < 0:
        return False
    if candidate > 255:
        return False
    return True


def is_recognized_g_node_status(candidate):
    try:
        GNodeStatus(candidate)
    except ValueError:
        return False
    return True


def is_market_alias_lrd_format(candidate):
    try:
        x = candidate.split('.')
    except AttributeError:
        return False
    try:
        MarketType(x[0])
    except ValueError:
        return False
    g_node_alias = ".".join(x[1:])
    return is_g_node_lrd_alias_format(g_node_alias)
    

def is_market_slot_alias_lrd_format(candidate):
    try:
        x = candidate.split('.')
    except AttributeError:
        return False
    slot_start = x[-1]
    if len(slot_start) != 10:
        return False
    try:
        slot_start = int(slot_start)
    except ValueError:
        return False
    if slot_start % 300 != 0:
        return False
        
    market_alias_lrd = ".".join(x[:-1])
    if not is_market_alias_lrd_format(market_alias_lrd):
        return False
    
    market_type = PlatformMarketType[market_alias_lrd.split('.')[0]]
    if not slot_start % (market_type.market_slot_duration_minutes * 60) == 0:
        print(f"market_slot_start_s mod {(market_type.market_slot_duration_minutes * 60)} must be 0")
        return False

    return True
    

def is_simple60(candidate):
    return True


def is_simple_cron24(candidate):
    return True


def is_valid_historical_temp_type(candidate):
    if candidate == 'X':
        return True
    elif isinstance(candidate,float):
        return True
    else:
        return False