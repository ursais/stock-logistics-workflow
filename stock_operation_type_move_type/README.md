# Stock Logistic Workflow - Configurable Move Type

This module allows configuring the default move_type (Shipping Policy) on Operation Types (stock.picking.type).

## Features

- Add `default_move_type` field to `stock.picking.type`
- Use operation type default when creating pickings
- Maintain backward compatibility
- User-friendly configuration in Operation Type form

## Usage

1. Go to Inventory > Configuration > Operation Types
2. Select or create an Operation Type
3. Set the "Default Shipping Policy" field:
   - "As soon as possible" - Partial deliveries allowed
   - "When all products are ready" - Complete delivery only
4. Save the configuration

New pickings created with this operation type will automatically use the configured shipping policy.

## Technical Details

### Model Changes

**stock.picking.type**
- Added `default_move_type` field with selection options
- Default value: 'direct' (As soon as possible)
- Required field with proper help text

**stock.picking**
- Modified `move_type` field to remove hardcoded default
- Override `create()` method to use operation type default
- Fallback to 'direct' if no operation type or default configured

### Installation

The module automatically sets the default_move_type to 'direct' for all existing operation types during installation.

### Compatibility

- Odoo 17.0+
- Depends on `stock` module
- Maintains full backward compatibility
