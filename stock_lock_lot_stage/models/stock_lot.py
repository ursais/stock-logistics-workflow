# Copyright 2025 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    locked = fields.Boolean(
        compute="_compute_locked",
        inverse="_inverse_locked",
        store=True,
    )

    stage_id = fields.Many2one(
        "stock.lot.stage",
        string="Stage",
        tracking=True,
        default=lambda self: self._default_stage_id(),
        group_expand="_read_group_stage_ids",
        index=True,
    )
    partial_approved_qty = fields.Float(
        string="Partial Approved Quantity",
        help="Maximum quantity allowed in locations that don't allow locked lots."
        "Leave zero to approve the full quantity.",
        tracking=True,
    )
    usable_location_qty = fields.Float(
        compute="_compute_usable_location_qty",
        help="Total quantity in locations where locked lots are not allowed.",
    )

    def _default_stage_id(self):
        return self.env["stock.lot.stage"].search([], limit=1)

    @api.depends("stage_id.locked")
    def _compute_locked(self):
        for lot in self:
            lot.locked = lot.stage_id.locked

    def _inverse_locked(self):
        for lot in self:
            stage = lot._get_stage_for_locked(lot.locked)
            if stage and stage != lot.stage_id:
                lot.stage_id = stage

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return stages.search([], order=order)

    @api.depends("quant_ids.quantity", "quant_ids.location_id")
    def _compute_usable_location_qty(self):
        for lot in self:
            lot.usable_location_qty = sum(
                lot.quant_ids.filtered(
                    lambda q: not q.location_id.allow_locked
                    and q.location_id.usage == "internal"
                ).mapped("quantity")
            )

    @api.constrains("stage_id")
    def _check_stage_change(self):
        if not self.user_has_groups("stock_lock_lot.group_lock_lot"):
            raise exceptions.AccessError(_("You are not allowed to change lot stages."))

    @api.constrains("stage_id", "partial_approved_qty")
    def _check_partial_qty_stage_compatibility(self):
        """Check that partial approved quantity is compatible with the current stage."""
        for lot in self.filtered("stage_id"):
            # Partial qty is only rejected in unlocked stages that don't allow
            # partial approval
            if lot.stage_id.locked:
                continue
            if lot.partial_approved_qty > 0 and not lot.stage_id.allow_partial_approved:
                raise exceptions.ValidationError(
                    _(
                        "Partial approved quantity can only be set "
                        "on lots in stages that allow it. "
                        "Lot '%(lot)s' has a partial approved quantity "
                        "but is in stage '%(stage)s' which doesn't allow it. "
                        "Either clear the partial approved quantity "
                        "or move the lot to a stage that allows partial approval.",
                        lot=lot.name,
                        stage=lot.stage_id.name,
                    )
                )

            # Unlocked stages that allow partial approval must have partial qty set
            if lot.partial_approved_qty == 0 and lot.stage_id.allow_partial_approved:
                raise exceptions.ValidationError(
                    _(
                        "Lots in stage '%(stage)s' must have "
                        "a partial approved quantity set. "
                        "Please set a partial approved quantity "
                        "or move the lot to a different stage.",
                        stage=lot.stage_id.name,
                    )
                )

    @api.constrains("partial_approved_qty")
    def _check_partial_approved_qty(self):
        if not self.user_has_groups("stock_lock_lot.group_lock_lot"):
            raise exceptions.AccessError(
                _("You are not allowed to change the partial approved quantity.")
            )

        # Validate that partial approved quantity is not negative
        if any(lot.partial_approved_qty < 0 for lot in self):
            raise exceptions.ValidationError(
                _("Partial approved quantity cannot be negative.")
            )

        # Run quant validation to ensure current quantities don't exceed the new limit
        lots_to_check = self.filtered("partial_approved_qty")
        lots_to_check.quant_ids._check_partial_approved_qty()

    def _get_stage_for_locked(self, locked):
        """Return the first stage matching the locked value."""
        return self.env["stock.lot.stage"].search([("locked", "=", locked)], limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)
        for lot in lots:
            if not lot.stage_id or lot.stage_id == self._default_stage_id():
                stage = lot._get_stage_for_locked(lot.locked)
                if stage and stage != lot.stage_id:
                    lot.stage_id = stage
        return lots
