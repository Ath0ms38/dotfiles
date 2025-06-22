#!/usr/bin/env -S ags run

import { App, Widget } from "astal/gtk3"
import CalendarWidget from "./widgets/Calendar"

// --- On-demand popup management ---
const popupStates = {
    calendar: false,
};
const popupWindows: { [key: string]: any } = {};

function createPopup(name: string, WidgetComponent: any, position: { anchor: string[], marginTop?: number, marginRight?: number, marginBottom?: number }) {
    if (popupWindows[name]) return;
    print(`Creating popup: ${name}`);
    
    popupWindows[name] = new Widget.Window({
        name: `${name}-popup`,
        className: "popup-window anime-room-theme",
        visible: true,
        anchor: position.anchor,
        layer: "overlay",
        marginTop: position.marginTop || 0,
        marginRight: position.marginRight || 0,
        marginBottom: position.marginBottom || 0,
        keymode: "on-demand",
        setup: (self: any) => {
            self.connect("key-press-event", (_: any, event: any) => {
                if (event.get_keyval()[1] === 65307) { // Escape key
                    destroyPopup(name);
                }
            });
            
            // Click outside to close
            self.connect("button-press-event", (_: any, event: any) => {
                // Check if click is outside the popup content
                const [x, y] = event.get_coords();
                const allocation = self.get_allocation();
                if (x < 0 || y < 0 || x > allocation.width || y > allocation.height) {
                    destroyPopup(name);
                }
            });
            
            self.connect("destroy", () => {
                print(`Destroyed popup: ${name}`);
                popupWindows[name] = null;
                popupStates[name] = false;
            });
        },
        child: new Widget.Box({
            className: "popup-window-box",
            child: WidgetComponent({ fullView: true })
        }),
    });
    popupStates[name] = true;
}

function destroyPopup(name: string) {
    if (popupWindows[name]) {
        print(`Destroying popup: ${name}`);
        popupWindows[name].destroy();
        popupWindows[name] = null;
        popupStates[name] = false;
    }
}

function togglePopup(name: string, WidgetComponent: any, position: { anchor: string[], marginTop?: number, marginRight?: number, marginBottom?: number }) {
    if (popupStates[name]) {
        destroyPopup(name);
    } else {
        // Close all others
        Object.keys(popupWindows).forEach(key => destroyPopup(key));
        createPopup(name, WidgetComponent, position);
    }
}

print("Using CSS: ./style.css")
App.start({
    css: "./style.css",

    requestHandler(request: string, res: (response: any) => void) {
        const [action] = request.split(' ');
        
        // Position popups below waybar (waybar height is 42px + 8px margin-top = 50px)
        const positions = {
            calendar: { 
                anchor: ["top", "right"], 
                marginTop: 50,  // Below waybar
                marginRight: 20  // Some padding from right edge
            },
        };
        
        const widgetMap: Record<string, [any, string]> = {
            "toggle_calendar": [CalendarWidget, "calendar"],
        };
        
        if (widgetMap[action]) {
            const [WidgetComponent, key] = widgetMap[action];
            togglePopup(key, WidgetComponent, positions[key]);
            res(`${action} ${popupStates[key] ? 'shown' : 'hidden'}`);
        } else {
            res({ status: "error", message: "Unknown request" });
        }
    },

    main() {
        // No popups are created at startup!
        // They will be created on-demand when requested
    }
})
