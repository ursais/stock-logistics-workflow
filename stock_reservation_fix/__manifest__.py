# -*- coding: utf-8 -*-
{
    'name': 'Stock Reservation Fix',
    'version': '16.0.1.0.0',
    'category': 'Stock',
    'summary': 'Fix stock reservation discrepancies when unreserving more stock than available',
    'description': """
        This module provides a server action to fix stock reservation discrepancies
        that occur when trying to unreserve more stock than is physically available.
        It safely adjusts reserved quantities to match available stock.
    """,
    'author': 'Open Source Integrators',
    'website': 'https://www.opensourceintegrators.com',
    'license': 'AGPL-3',
    'depends': ['stock'],
    'data': [
        'data/ir_actions_server.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
