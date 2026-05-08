## Roadmap

### v18.0

- The standard Odoo field `scrap_reason_tag_ids` has been made invisible to prevent functional overlap with this module.

### v19.0

- `stock.location.scrap_location` was removed; reason-code scrap destinations use `usage = inventory` (aligned with core `stock.scrap`).
- `stock.move.scrapped` was removed; the move form shows `reason_code_id` when `scrap_id` is set.
- Standard `scrap_reason_tag_ids` remains hidden on scrap forms to avoid duplicate semantics with structured reason codes.
