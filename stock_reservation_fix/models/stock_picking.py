# -*- coding: utf-8 -*-

import logging

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_fix_reservation_discrepancy(self):
        """
        Fix stock reservation discrepancies by adjusting reserved quantities
        to match available stock. This method checks each move's reserved
        quantity against available stock and adjusts move lines accordingly.

        This is useful when trying to void/cancel a picking that has
        reservations exceeding available stock.

        The method works by:
        1. Checking each move's reserved_availability against available stock
        2. If reserved exceeds available, reducing move line quantities
        3. This allows the picking to be voided/cancelled normally

        :return: dict with action result
        """
        self.ensure_one()

        if self.state not in ('draft', 'waiting', 'assigned', 'confirmed'):
            raise UserError(_(
                'Cannot fix reservations for picking %s in state %s. '
                'Only draft, waiting, assigned, or confirmed pickings can be fixed.'
            ) % (self.name, self.state))

        fixed_moves = []
        total_adjustments = 0

        for move in self.move_ids:
            if move.state not in ('draft', 'waiting', 'assigned', 'confirmed'):
                continue

            # Get reserved quantity from move (computed field)
            reserved_qty = move.reserved_availability
            if float_is_zero(reserved_qty, precision_rounding=move.product_id.uom_id.rounding):
                continue

            # Get available stock for the product at the source location
            # Calculate available as: total quantity - reserved quantity in quants
            # Note: This move's reservations are already included in quant reserved_quantity
            quants = self.env['stock.quant']._gather(
                move.product_id,
                move.location_id,
            )
            total_qty = sum(quants.mapped('quantity'))
            total_reserved_in_quants = sum(quants.mapped('reserved_quantity'))
            
            # Available stock = total - reserved by all moves
            # But if this move is trying to reserve more than available,
            # we need to reduce it. The issue occurs when move lines claim
            # more reservation than quants can provide.
            # So we calculate: what's the maximum we can reserve?
            # It's: total_qty - (reserved_in_quants - this_move_reserved) = total_qty - reserved_in_quants + reserved_qty
            # But actually, the simpler approach: if reserved_qty > (total_qty - reserved_in_quants + reserved_qty),
            # that means reserved_qty > total_qty, which shouldn't happen.
            # The real issue is: move lines claim X, but when trying to unreserve,
            # quants don't have X reserved. So we should reduce to match what's actually possible.
            # For safety, we'll reduce to match available stock (total - reserved by others)
            available_qty = total_qty - total_reserved_in_quants + reserved_qty

            # If reserved quantity exceeds what's physically possible (total stock),
            # we need to adjust to at most total stock
            if float_compare(reserved_qty, total_qty, precision_rounding=move.product_id.uom_id.rounding) > 0:
                # Move is trying to reserve more than total stock - reduce to total stock
                target_qty = total_qty
            elif float_compare(reserved_qty, available_qty, precision_rounding=move.product_id.uom_id.rounding) > 0:
                # Move is trying to reserve more than available - reduce to available
                target_qty = available_qty
            else:
                # No adjustment needed
                continue

            adjustment = self._adjust_move_reservation(move, target_qty)
            if adjustment > 0:
                fixed_moves.append({
                    'product': move.product_id.display_name,
                    'reserved': reserved_qty,
                    'available': available_qty,
                    'target': target_qty,
                    'adjusted': adjustment,
                })
                total_adjustments += adjustment

        if fixed_moves:
            message = _(
                'Fixed reservation discrepancies:\n'
            )
            for move_info in fixed_moves:
                message += _(
                    '\n- Product: %s\n'
                    '  Reserved: %s → Target: %s\n'
                    '  Adjusted by: %s'
                ) % (
                    move_info['product'],
                    move_info['reserved'],
                    move_info['target'],
                    move_info['adjusted'],
                )
            _logger.info(
                'Fixed reservation discrepancies for picking %s: %s',
                self.name,
                fixed_moves
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Reservation Fix Complete'),
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Issues Found'),
                    'message': _(
                        'No reservation discrepancies found for picking %s.'
                    ) % self.name,
                    'type': 'info',
                    'sticky': False,
                }
            }

    def _adjust_move_reservation(self, move, target_qty):
        """
        Adjust the reserved quantity for a move to match the target quantity.

        This method reduces the quantity on move lines to match the target
        quantity. When move lines are modified, Odoo automatically updates
        the quant reservations, allowing the picking to be voided/cancelled.

        :param move: stock.move record
        :param target_qty: float - target quantity in product UOM
        :return: float - amount adjusted (positive means reduced)
        """
        move.ensure_one()

        # Get move lines with reservations (quantity > 0)
        move_lines = move.move_line_ids.filtered(
            lambda ml: not float_is_zero(
                ml.quantity_product_uom,
                precision_rounding=ml.product_id.uom_id.rounding
            )
        )
        
        if not move_lines:
            return 0.0

        # Calculate total reserved from move lines
        reserved_qty = sum(move_lines.mapped('quantity_product_uom'))
        original_reserved = reserved_qty
        
        if float_compare(reserved_qty, target_qty, precision_rounding=move.product_id.uom_id.rounding) <= 0:
            return 0.0

        # Calculate adjustment needed
        adjustment_needed = reserved_qty - target_qty

        # Adjust move lines to reduce reserved quantity
        # Sort by quantity_product_uom descending to adjust largest first
        remaining_to_adjust = adjustment_needed
        sorted_move_lines = move_lines.sorted('quantity_product_uom', reverse=True)

        for move_line in sorted_move_lines:
            if float_compare(remaining_to_adjust, 0, precision_rounding=move.product_id.uom_id.rounding) <= 0:
                break

            current_qty_product_uom = move_line.quantity_product_uom
            if float_is_zero(current_qty_product_uom, precision_rounding=move.product_id.uom_id.rounding):
                continue

            # Calculate reduction needed
            reduction = min(current_qty_product_uom, remaining_to_adjust)
            new_qty_product_uom = current_qty_product_uom - reduction

            # Convert new quantity from product UOM to move line UOM
            # quantity_product_uom is computed from quantity, so we need to set quantity
            new_quantity = move_line.product_uom_id._compute_quantity(
                new_qty_product_uom,
                move_line.product_id.uom_id,
                rounding_method='HALF-UP'
            )

            if float_is_zero(new_qty_product_uom, precision_rounding=move.product_id.uom_id.rounding):
                # If quantity goes to zero, unlink the move line
                # This will automatically unreserve the quant via the unlink method
                move_line.unlink()
            else:
                # Reduce the quantity on the move line
                # This will trigger quant reservation updates via write method
                move_line.write({
                    'quantity': new_quantity,
                })

            remaining_to_adjust -= reduction

        # Verify the adjustment worked
        new_reserved_qty = sum(move.move_line_ids.mapped('quantity_product_uom'))
        actual_adjustment = original_reserved - new_reserved_qty

        return actual_adjustment
