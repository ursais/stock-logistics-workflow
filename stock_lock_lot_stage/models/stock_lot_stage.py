# Copyright 2025 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLotStage(models.Model):
    _name = "stock.lot.stage"
    _description = "Lot Stage"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    locked = fields.Boolean(
        help="If checked, lots in this stage are locked for use.",
    )
    allow_partial_approved = fields.Boolean(
        help="If checked, lots in this stage can have a partial approved quantity set. "
        "Only available for unlocked stages.",
    )
    fold = fields.Boolean(
        help="If checked, this stage will be folded in kanban views.",
    )
    active = fields.Boolean(default=True)

    @api.constrains("allow_partial_approved", "locked")
    def _check_allow_partial_approved(self):
        """Partial approval can only be set on unlocked stages."""
        for stage in self:
            if stage.allow_partial_approved and stage.locked:
                raise ValidationError(
                    _(
                        "Partially approved quantity can only be allowed on "
                        "unlocked stages."
                    )
                )
