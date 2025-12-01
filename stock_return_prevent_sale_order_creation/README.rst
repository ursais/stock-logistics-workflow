Stock Return Prevent Sale Order Creation
=========================================

This module prevents return pickings from automatically creating sales orders.

Problem
-------

When a return picking is created from a sales order delivery, it inherits the
procurement group from the original picking. If this procurement group is
linked to a sale order, the return picking can trigger procurement that
automatically creates a new sales order, requiring manual cancellation.

Solution
--------

This module overrides:

1. ``stock.return.picking`` wizard's ``_create_returns`` method to clear
   procurement groups linked to sale orders from return pickings when they
   are created.

2. ``stock.picking`` model's ``_action_confirm`` method to ensure return
   pickings don't have procurement groups linked to sale orders before
   confirmation, preventing procurement from being triggered.

Usage
-----

No configuration is required. The module automatically prevents return pickings
from triggering sales order creation.

Installation
------------

Install the module from the Apps menu. The module depends on ``stock`` and
``sale_stock``.

Bug Tracker
-----------

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/stock-logistics-workflow/issues>`_.

Credits
-------

Authors
~~~~~~~

* Open Source Integrators

Maintainers
~~~~~~~~~~~

This module is maintained by Open Source Integrators.
