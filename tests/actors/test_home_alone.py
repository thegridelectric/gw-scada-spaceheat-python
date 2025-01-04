


def test_home_alone():
    ...
    #  after trigger_house_cold_onpeak_event
    # all relays are direct reports of auto.h.onpeak-backup

    # If scada goes into Admin mode, 
    # HomeAlone top state is Dormant, normal state is Dormant
    # and len(homealone.my_actuators is 0)
    # and relay3 has handle admin.relay3

    # same as above but with atn:
    # relay3 has handle a.aa.relay3

