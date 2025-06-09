# MIS Color Picker Widget for Odoo

## Overview

The MIS Color Picker Widget is a custom field widget for Odoo that allows users to select colors using a modern and intuitive color picker. This widget supports both HEX & RGB color format and provides a set of popular colors for quick selection.


## Features

- Easy integration with Odoo forms
- Supports HEX color format by default
- Option to enable RGB color format
- Includes a set of popular colors for quick selection
- User-friendly interface with color preview
- Compatible with Odoo 14.0 and above

## Installation

1. Download the module from the Odoo App Store.
2. Extract the downloaded file to your Odoo addons directory.
3. Restart your Odoo server.
4. Update the app list by navigating to Apps > Update Apps List.
5. Search for "MIS Color Picker Widget" and install the module.

## Usage

1. Navigate to the form where you want to use the color picker widget.
2. Add a new field with the type "Char" to your model.
Example:
```python
from odoo import models, fields

class ColorModel(models.Model):
    _name = 'color.model'
    _description = 'Color Model'

    name = fields.Char(string='Name', required=True)
    color = fields.Char(string='Color')
```
3. In the form view, set the widget attribute of the field to "mis_color_picker".
Example:
```xml
<field name="color" widget="mis_color_picker"/>
```
4. Save the changes and refresh the form view. The color picker widget should now be available for the specified field.


## License
This module is licensed under the General Public License, Version 3 (LGPL v3). (https://www.gnu.org/licenses/lgpl-3.0-standalone.html)