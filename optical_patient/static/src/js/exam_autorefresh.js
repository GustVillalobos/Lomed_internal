/** @odoo-module **/

import { registry } from "@web/core/registry";
import { debounce } from "@web/core/utils/timing";
import { useService } from "@web/core/utils/hooks";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { onWillDestroy } from "@odoo/owl";

export class OpticExamKanbanController extends KanbanController {
    setup() {
        super.setup();

        //Detectando modo desarrollador
        const isDebugMode = odoo && odoo.debug;
        const devMenu = document.querySelector('.o_debug_manager_menu');

        //Configuración inicial
        this.bus = useService("bus_service");
        this.currReception = this.props.context?.default_reception_id;
        this.channelName = `consultorio_ch_${this.currReception || "default"}`;
        this.DEBUG = isDebugMode || devMenu;
        this._isDestroyed = false

        if (this.DEBUG) console.log("Modo desarrollador activado");

        if (!this.bus) {
            console.warn("bus_service no disponible aún");
            return;
        }

        //console.log("Canales:",this.bus);
        
        this.bus.addChannel(this.channelName);
            
        this.reloadKanban = debounce(async () => {

            try {
                if (this.model && this.model.load) {
                    if (!this._isDestroyed) {
                        if (this.DEBUG) console.log("Intentando refrescar vista Kanban...");
                        await this.model.load(); 
                        this.render(true); 
                        if (this.DEBUG) console.log("Vista Kanban actualizada");
                    }
                } else {
                    if (this.DEBUG) console.warn("this.model.load() no disponible, haciendo reload total");
                    if (!this._isDestroyed) window.location.reload();
                }
            } catch (err) {
                if (this._isDestroyed) console.error("Error al recargar vista Kanban:", err);
            }
        }, 1000);

        onWillDestroy(() => {
            this._isDestroyed = true;
            if (this.reloadKanban?.cancel) this.reloadKanban.cancel();

            if (this.bus && this.channelName) {
                this.bus.deleteChannel(this.channelName);
                if (this.onNotifyEvent) {
                    this.bus.removeEventListener("notification", this.onNotifyEvent);
                }
                if (this.DEBUG) console.log(`Canal ${this.channelName} liberado con onWillDestroy()`);
            }
        });

        this.onNotifyEvent = this._onNotifyEvent.bind(this);
        this.bus.addEventListener("notification", this.onNotifyEvent);
        if (this.DEBUG) console.log(`Suscrito al canal: ${this.channelName}`);
    }

    _onNotifyEvent(event) {
        const payload = event?.detail;
        if (!Array.isArray(payload)) return;
        for (const notif of payload) {
            const data = notif?.type;
            if (data?.type === "optic.exam_updated" && data?.reception_id == this.currReception) {
                if (this.DEBUG) console.log("Notificación recibida:", notif);
                this.reloadKanban();
            }
        }
    }

    destroy() {
        this._isDestroyed = true

        if (this.reloadKanban && this.reloadKanban.cancel){
            this.reloadKanban.cancel();
        }

        if (this.bus) {
            if (this.channelName) {
                this.bus.deleteChannel(this.channelName);
            }
            if (this.bus._opticExamBound && this.onNotifyEvent) {
                this.bus.removeEventListener("notification", this.onNotifyEvent);
                delete this.bus._opticExamBound;
            }
            if (this.DEBUG) console.log(`Canal liberado: ${this.channelName}`);
        }
        super.destroy();
    }
}

registry.category("views").add(
    "optic_exam_autorefresh",
    Object.assign({}, registry.category("views").get("kanban"), {
        Controller: OpticExamKanbanController,
    })
);