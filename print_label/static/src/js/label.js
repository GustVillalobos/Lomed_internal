/** @odoo-module **/

import { registry } from "@web/core/registry";

let selected_device = null;
const isDebugMode = odoo && odoo.debug;

function getPrinter() {
    return new Promise((resolve, reject) => {
        if (selected_device) {
            if(isDebugMode) console.log("Verificando información de impresor")
            resolve(selected_device);
            return;
        }

        BrowserPrint.getDefaultDevice(
            "printer",
            function (device) {
                selected_device = device;
                if(isDebugMode) console.log("Impresor detectado: ",selected_device)
                resolve(device);
            },
            function (error) {
                console.error("Error al obtener impresora:", error);
                reject(error);
            }
        );
    });
}

async function writeToSelectedPrinter(dataToWrite) {
    try {
        const printer = await getPrinter();

        if(isDebugMode) console.log("Iniciando proceso de impresión")
        printer.send(
            dataToWrite,
            undefined,
            function (errorMessage) {
                console.error("Error al imprimir:", errorMessage);
            }
        );
        if(isDebugMode) console.log("Proceso realizado correctamente")
    } catch (error) {
        console.error("Excepción al imprimir:", error);
    }
}

registry.category("actions").add("print_label_action", async (env, action) => {
    if (!action.context.zpl) {
        console.warn("No se encontró ZPL en el contexto");
        return;
    }
    await writeToSelectedPrinter(action.context.zpl);
});