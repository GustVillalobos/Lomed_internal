{
    "name": "MIS Color Picker Widget",
    "version": "16.0.1.0.0",
    "summary": "MIS Color Picker Widget",
    "description": """
        The Color Picker Widget is a custom field widget for Odoo that allows users to select colors using a modern and intuitive color picker. This widget supports both HEX and RGB color formats and provides a set of popular colors for quick selection.
        Features :
        - Easy integration with Odoo forms
        - Supports HEX color format by default
        - Option to enable RGB color format
        - Includes a set of popular colors for quick selection
        - User-friendly interface with color preview
        - Compatible with Odoo 14.0 and above
    """,
    "category": "Tools",
    "license": "LGPL-3",
    "author": "Mandiri Inovasi Solusi",
    "website": "https://i-solusi.com",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "mis_color_picker/static/src/lib/nano.min.css",
            "mis_color_picker/static/src/lib/pickr.min.js",
            "mis_color_picker/static/src/js/color_picker.js",
            "mis_color_picker/static/src/xml/color_picker_template.xml",
        ],
    },
    "images": ["static/description/color_picker.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
