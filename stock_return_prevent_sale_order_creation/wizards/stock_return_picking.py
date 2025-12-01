# Copyright 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockReturnPicking(models.TransientModel):
    """
    Override stock.return.picking to prevent return pickings from
    inheriting procurement groups that are linked to sale orders.
    This prevents automatic sales order recreation when returns are processed.
    """

    _inherit = "stock.return.picking"

    def _create_returns(self):
        """
        Override to clear procurement group from return pickings
        if the group is linked to sale orders.
        This prevents return pickings from triggering procurement
        that would create new sales orders.
        
        Returns:
            tuple: (new_picking_id, new_picking_type_id) as returned by super()
        """
        new_picking_id, new_picking_type_id = super()._create_returns()
        
        if new_picking_id:
            new_picking = self.env["stock.picking"].browse(new_picking_id)
            
            # Check if the return picking has a procurement group linked to sale orders
            # Return pickings should not inherit procurement groups that trigger
            # sales order creation, as returns are reversals, not new orders
            if new_picking.group_id and new_picking.group_id.sale_ids:
                # Clear the procurement group from return picking moves
                # to prevent automatic sales order creation
                new_picking.move_ids.write({"group_id": False})
                # Also clear from the picking itself
                new_picking.group_id = False
        
        return new_picking_id, new_picking_type_id
