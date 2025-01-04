"""Type new.command.tree, version 000"""

from typing import List, Literal

from gwproto.named_types.spaceheat_node_gt import SpaceheatNodeGt
from gwproto.property_format import LeftRightDotStr, UTCMilliseconds
from pydantic import BaseModel, field_validator


class NewCommandTree(BaseModel):
    FromGNodeAlias: LeftRightDotStr
    ShNodes: List[SpaceheatNodeGt]
    UnixMs: UTCMilliseconds
    TypeName: Literal["new.command.tree"] = "new.command.tree"
    Version: Literal["000"] = "000"

    @field_validator("ShNodes")
    @classmethod
    def check_sh_nodes(cls, v: List[SpaceheatNodeGt]) -> List[SpaceheatNodeGt]:
        """
            Axiom 1: ShNode hierarchy consistencies.
            Handles and ActorHierarchyNames are closed under prefixes. That is, for every handle in
        the set of handles, all of its prefixes (as generated by handle.split(".")[:n] for any n)
        are also in the set of handles.
        """
        # Implement Axiom(s)
        return v