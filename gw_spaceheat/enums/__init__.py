"""
GridWorks Enums used in scada, the Application Shared Language (ASL) used by SCADA
devices and AtomicTNodes to communicate with each other. These enums play a specific structural
role as semantic "glue" within ASLs.

Application Shared Languages are an evolution of the concept of Application Programming Interfaces.
In a nutshell, an API can be viewed as a rather restricted version of an SAL, where only one application
has anything complex/interesting to say and, in general, the developers/owners of that application
have sole responsibility for managing the versioning and changing of that API. Note also that SALs
do not make any a priori assumption about the relationship (i.e. the default client/server for an API)
or the message delivery mechanism (i.e. via default GET/POST to RESTful URLs). For more information
on these ideas:
  - [GridWorks Enums](https://gridwork-type-registry.readthedocs.io/en/latest/types.html)
  - [GridWorks Types](https://gridwork-type-registry.readthedocs.io/en/latest/types.html)
  - [ASLs](https://gridwork-type-registry.readthedocs.io/en/latest/asls.html)
 """

from gw.enums import MarketTypeName
from enums.home_alone_top_state import HomeAloneTopState
from enums.main_auto_event import MainAutoEvent
from enums.main_auto_state import MainAutoState
from enums.market_price_unit import MarketPriceUnit
from enums.market_quantity_unit import MarketQuantityUnit
from enums.pico_cycler_event import PicoCyclerEvent
from enums.pico_cycler_state import PicoCyclerState
from enums.top_event import TopEvent
from enums.top_state import TopState


__all__ = [
    "MarketTypeName",
    "HomeAloneTopState",  # [home.alone.top.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#homealonetopstate)
    "MainAutoEvent",  # [main.auto.event.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#mainautoevent)
    "MainAutoState",  # [main.auto.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#mainautostate)
    "MarketPriceUnit",  # [market.price.unit.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#marketpriceunit)
    "MarketQuantityUnit",  # [market.quantity.unit.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#marketquantityunit)
    "PicoCyclerEvent",  # [pico.cycler.event.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#picocyclerevent)
    "PicoCyclerState",  # [pico.cycler.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#picocyclerstate)
    "TopEvent",  # [top.event.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#topevent)
    "TopState",  # [top.state.000](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#topstate)
]
