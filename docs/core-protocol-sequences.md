# Core Scada protocol message sequences

This document gives a high-level sketch of core message flows between the Scada, the Atomic Transactive Node (`Atn`)
and various other "actors" running on the Scada or in the home. 

What we describe below are standard patterns of messages, where one message will (usually) trigger the next


### Meter aggregate power change

    Meter   ->  PowerWatts                       ->  Scada 
    Scada   ->  PowerWatts                       ->  Atn            

See description [here](https://github.com/thegridelectric/gw-scada-spaceheat-python/blob/main/gw_spaceheat/actors/scada.py#L253).

Milliseconds matter for Scada responsiveness with PowerWatts. The Scada will not, for example, request an ack
from the `Atn` for receipt of the `PowerWatts`. Note also that the `PowerWatts` does not have a timestamp.


### Scada  Status report

    Scada   ->  GtShStatus                  ->  Atn
    Scada   ->  SnapshotSpaceheat           ->  Atn

The `GtShStatus` message contains all the telemetry updates received by the Scada in the last 5 minutes.
The `SnapshotSpaceheat` contains the latest telemetry status for all known telemetry points.


### SimpleSensor periodic telemetry

    SimpleSensor  ->  GtTelemetry                 ->  Scada           

This telemetry will be included in the next `GtShStatus` message.

### Meter asynchronous telemetry

    Meter   ->  GtShTelemetryFromMultipurposeSensor                  ->  Scada 
    
The primary power meter is the most important example of a [multipurpose sensors](docs/multipurpose-sensor.md). 

The trigger for the power meter reporting a new power reading is a fractional change of the maximum rated power. 
FILL THIS IN.

### Atn sends a finite state machine trigger

    Atn     ->  FsmTriggerFromAtn           ->  Scada

    (As long as the `Atn-Scada dispatch contract is live) 

    Scada then unpacks this and sends it down the appropriate hierarchy 
    in the finites state machine

    Scada   ->  FsmEvent     ->  Level1FsmNode

    This process continues down to a leaf node in the fsm:

    Level3FsmNode   ->  FsmEvent      ->  RelayNode


A relay or other driver that can actually change the physical state of the system is 
always a 'leaf' node in the hierarchical finite state machine.  For now we'll assume
its a simple relay. It has three core functions. It waits for events from its (single) parent, and tracks the state of the relay, and as best as it can it makes sure that the state of its relay matches its internal model of its state machine.  

The Fsms also produce a series of reports to track the Events, Transitions, and Actions caused by the triggering events. 

     Level1FsmNode -> FsmAtomicReport -> Scada
     Level2FsmNode -> FsmAtomicReport -> Scada
     Level3FsmNode -> FsmAtomicReport -> Scada
     RelayNode -> FsmAtomicReport -> Scada

In addition, the final relay node - which has actually made a physical state change
by actuating a relay (we hope) will send a  GtTelemetry message is sent as a result of sensing the state:
     RelayNode -> GtTelemetry -> Scada

Assuming the relay follows the command from the Scada _and_ the state of the relay does 
in fact change, an atn FsmTriggerFromAtn to turn on a relay will be followed shortly by a GtTelemetry from the relay (as well as independent verification from the power meter)

### Atn requests status

    Atn     ->  GtShCliAtnCmd               ->  Scada
    Scada   ->  SnapshotSpaceheat           ->  Atn
    Scada   ->  Status           ->  Atn

This a maintenance command for humans to immediately see `SnapshotSpaceheat` from the Scada instead of 
waiting for 5 minutes. 

### HomeAlone sends a finite state machine trigger

When the dispatch contract is not live, the scada's handle changes from
`a.s` to `h.s` - to reflect that it is now receiving fsm state change triggers only from the HomeAlone actor, instead of the remote AtomicTnode. Since the parent node
is local it can trigger events directly with an FsmEvent message, which will
then start the same csscade as described 

    Home    ->  FsmEvent      -> Scada

