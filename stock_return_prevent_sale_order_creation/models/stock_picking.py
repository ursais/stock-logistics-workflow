# Copyright 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    """
    Override stock.picking to ensure return pickings don't trigger
    sales order creation through procurement groups.
    """

    _inherit = "stock.picking"

    def _action_confirm(self):
        """
        Override to clear procurement groups linked to sale orders
        from return pickings before confirmation.
        This prevents return pickings from triggering procurement
        that would create new sales orders.
        """
        # Identify return pickings by checking if any move has origin_returned_move_id
        # Return pickings are created from return wizard and have this relationship
        return_pickings = self.filtered(
            lambda p: p.move_ids.origin_returned_move_id
            and p.group_id
            and p.group_id.sale_ids
        )
        
        if return_pickings:
            # Clear procurement groups from return picking moves
            # to prevent automatic sales order creation
            return_pickings.move_ids.write({"group_id": False})
            # Clear from pickings themselves
            return_pickings.write({"group_id": False})
        
        return super()._action_confirm()
