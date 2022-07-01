"""gt.sh.cli.scada.response.100 type"""

from schema.errors import MpSchemaError
from schema.gt.gt_sh_cli_scada_response.gt_sh_cli_scada_response_base import (
    GtShCliScadaResponseBase,
)


class GtShCliScadaResponse(GtShCliScadaResponseBase):
    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(
                f" Errors making making gt.sh.cli.scada.response.100 for {self}: {errors}"
            )

    def hand_coded_errors(self):
        return []
