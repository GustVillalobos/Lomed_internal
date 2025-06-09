/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// Ensure Pickr is available globally
const Pickr = window.Pickr;

class ColorPickerField extends Component {
    static template = "ColorPickerWidgetTemplate";

    setup() {
        this.state = useState({ color: this.props.value || "#FFFFFF" });
        this.inputRef = useRef("input");
        this.destroyed = false;

        onMounted(() => {
            const input = this.inputRef.el;
            if (input) {
                this.pickr = Pickr.create({
                    el: input,
                    theme: 'nano',
                    default: this.state.color,
                    swatches: [
                        '#00BCD4', '#009688', '#03A9F4', '#2196F3', '#3F51B5', 
                        '#4CAF50', '#607D8B', '#673AB7', '#795548', '#8BC34A', 
                        '#9C27B0', '#9E9E9E', '#CDDC39', '#E91E63', '#F44336', 
                        '#FF5722', '#FF9800', '#FFB6C1', '#FFC107', '#FFEB3B', 
                        '#FFA07A'
                    ],
                    components: {
                        preview: true,
                        opacity: false,
                        hue: true,
                        interaction: {
                            hex: true,
                            rgba: true,
                            input: true,
                            clear: false,
                            save: true
                        }
                    }
                });

                const updateColor = (color) => {
                    const hexColor = color ? color.toHEXA().toString() : "#FFFFFF";
                    if (!this.destroyed) {
                        this.state.color = hexColor;
                        this.props.update(hexColor);
                    }
                };

                this.pickr.on('change', (color) => requestAnimationFrame(() => updateColor(color)));
                this.pickr.on('save', (color) => {
                    requestAnimationFrame(() => {
                        updateColor(color);
                        this.pickr.hide();
                    });
                });

                // Disable color picker when field is clicked in tree view
                input.addEventListener('click', (event) => {
                    if (this.isInTreeView()) {
                        event.stopPropagation();
                        this.pickr.disable();
                    } else {
                        this.pickr.enable();
                    }
                }, { passive: true });
            }
        });

        onWillUnmount(() => {
            this.destroyed = true;
            if (this.pickr) {
                this.pickr.destroyAndRemove();
            }
        });
    }

    willUpdateProps(nextProps) {
        if (nextProps.value !== this.props.value) {
            this.state.color = nextProps.value || "#FFFFFF";
            if (this.pickr) {
                this.pickr.setColor(this.state.color);
            }
        }
    }

    isInTreeView() {
        // Implement logic to determine if the field is in a tree view
        // This is a placeholder and should be replaced with actual logic
        return this.props.isTreeView || false;
    }
}

// Register the component in the Odoo registry
registry.category("fields").add("mis_color_picker", ColorPickerField);