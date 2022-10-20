import uuid

import pendulum
import gwproto


def test_property_format():
    assert gwproto.property_format.is_bit(0)
    assert gwproto.property_format.is_bit(1)
    assert not gwproto.property_format.is_bit(2)

    assert gwproto.property_format.is_64_bit_hex("12345abc")
    assert not gwproto.property_format.is_64_bit_hex("12345abcd")
    assert not gwproto.property_format.is_64_bit_hex("1234567g")

    assert not gwproto.property_format.is_lrd_alias_format(5)
    assert not gwproto.property_format.is_lrd_alias_format("5.a-h")
    assert gwproto.property_format.is_lrd_alias_format("a.s")

    bad_date_1 = pendulum.datetime(year=3000, month=1, day=1, hour=1)
    bad_date_2 = pendulum.datetime(year=1999, month=12, day=31, hour=23)
    good_date = pendulum.datetime(year=2200, month=1, day=1, hour=1)

    assert not gwproto.property_format.is_reasonable_unix_time_ms(bad_date_1.timestamp() * 1000)
    assert not gwproto.property_format.is_reasonable_unix_time_ms(bad_date_2.timestamp() * 1000)
    assert not gwproto.property_format.is_reasonable_unix_time_ms(good_date.timestamp())
    assert gwproto.property_format.is_reasonable_unix_time_ms(good_date.timestamp() * 1000)

    assert gwproto.property_format.is_reasonable_unix_time_s(good_date.timestamp())
    assert not gwproto.property_format.is_reasonable_unix_time_s(good_date.timestamp() * 1000)
    assert not gwproto.property_format.is_reasonable_unix_time_s(bad_date_1.timestamp())
    assert not gwproto.property_format.is_reasonable_unix_time_s(bad_date_2.timestamp())

    assert gwproto.property_format.is_unsigned_short(0)
    assert gwproto.property_format.is_unsigned_short(65535)
    assert not gwproto.property_format.is_unsigned_short(65536)
    assert not gwproto.property_format.is_unsigned_short(-1)

    assert gwproto.property_format.is_short_integer(-32768)
    assert gwproto.property_format.is_short_integer(32767)
    assert not gwproto.property_format.is_short_integer(-32769)
    assert not gwproto.property_format.is_short_integer(32768)

    s = "d4be12d5-33ba-4f1f-b9e5-2582fe41241d"
    assert gwproto.property_format.is_uuid_canonical_textual(s)
    assert not gwproto.property_format.is_uuid_canonical_textual(uuid.uuid4())
    fail1 = "d4be12d5-33ba-4f1f-b9e5"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail1)
    fail2 = "d4be12d-33ba-4f1f-b9e5-2582fe41241d"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail2)
    fail3 = "k4be12d5-33ba-4f1f-b9e5-2582fe41241d"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail3)
    fail4 = "d4be12d5-33a-4f1f-b9e5-2582fe41241d"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail4)
    fail5 = "d4be12d5-33ba-4f1-b9e5-2582fe41241d"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail5)
    fail6 = "d4be12d5-33ba-4f1f-b9e-2582fe41241d"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail6)
    fail7 = "d4be12d5-33ba-4f1f-b9e5-2582fe41241"
    assert not gwproto.property_format.is_uuid_canonical_textual(fail7)
