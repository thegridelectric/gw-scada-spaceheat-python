## Architecture Overview

The SCADA does 5 main things:

1) It keeps track of the state of a DispatchContract that it can hold with its AtomicTNode.

2) When the DispatchContract exists and is in RemoteControl mode, it sends up sensing data to its AtomicTNode:
    a) compressed state data (mostly temperature) sent up every 5 minutes
    b) asynchronous power reporting on change
    c) debugging information etc if sensors are broken

3) When the DispatchContract exists and is active, it responds to actuating commands from the AtomicTNode. This will primarily be for the main heating elements (heat pump, boost elements) 
but can also be for other devices that can be actuated, like circulator pumps and flow valves.

4) When the DispatchContract either does not exist or it exists but is in LocalControl mode, it 
runs the heating system.

5) It keeps a pared-down version of its compressed synchronous data when it doesn't have a DispatchContract running in RemoteControl, and sends that data up when the RemoteControl begins 
again. There are different standards for how and what to keep for 1 day, 7 days and 28 days.

The code needs to be prepared for a wide range of heating system configurations and sensor/actuator
choices. The thermal store may be water-based, or a phase change material. We may or may not be able
to control the COP/output temp tradeoff in the heat pump. We may end up adding new actuating devices
as we evaluate the heating system performance.

The code will be running on a handful of houses in Maine for the winter of 2022-2023.


Please go to gw_spaceheat/README.md for application readme.

Other files and subfolders are related to code derivation using https://effortlessapi.com/ effortlessapi tools.