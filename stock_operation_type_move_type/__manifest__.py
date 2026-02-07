{
    'name': 'Stock Logistic Workflow - Configurable Move Type',
    'version': '17.0.1.0.0',
    'summary': 'Configure default move_type on Operation Types',
    'description': """
        This module allows configuring the default move_type (Shipping Policy) 
        on Operation Types (stock.picking.type). Instead of having a hardcoded 
        default of 'direct' (As soon as possible), each operation type can have 
        its own default shipping policy.
        
        Features:
        - Add default_move_type field to stock.picking.type
        - Use operation type default when creating pickings
        - Maintain backward compatibility
        - User-friendly configuration in Operation Type form
    """,
    'author': 'Open Source Integrators',
    'website': 'https://github.com/OCA/stock-logistics-workflow',
    'license': 'LGPL-3',
    'category': 'Warehouse Management',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_type_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 100,
}
