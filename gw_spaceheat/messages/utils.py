import datetime
import pytz

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