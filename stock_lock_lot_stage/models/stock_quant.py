# Copyright 2025 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains("quantity", "lot_id")
    def _check_partial_approved_qty(self):
        """Validate that total lot quantity in restricted locations
        doesn't exceed partial approved quantity."""
        # Allow bypass for specific operations (similar to stock_no_negative)
        if self.env.context.get("skip_partial_approved_qty_check"):
            return

        # Filter quants that need validation
        quants_to_check = self.filtered(
            lambda q: q.quantity > 0
            and q.lot_id
            and q.lot_id.partial_approved_qty > 0
            and not q.location_id.allow_locked
        )

        for quant in quants_to_check:
            # Get current usable quantity - invalidate cache to ensure we get the
            # latest value since this constraint runs during a quantity
            # change, the computed field might still have the old cached
            # value before this quant's update
            quant.lot_id.invalidate_recordset()
            total_usable_qty = quant.lot_id.usable_location_qty

            # Validate against partial approved quantity
            if total_usable_qty > quant.lot_id.partial_approved_qty:
                raise ValidationError(
                    _(
                        "Cannot validate this stock operation because the total "
                        "quantity of lot '%(lot)s' (%(total).2f) in locations "
                        "that don't allow locked lots exceeds the partial "
                        "approved quantity (%(approved).2f).\n"
                        "Location: %(location)s\n"
                        "Move excess quantities to locations that allow locked lots "
                        "or increase the partial approved quantity.",
                        lot=quant.lot_id.name,
                        total=total_usable_qty,
                        approved=quant.lot_id.partial_approved_qty,
                        location=quant.location_id.complete_name,
                    )
                )
