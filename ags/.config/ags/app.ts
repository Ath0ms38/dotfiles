#!/usr/bin/env -S ags run

import { App, Widget, Astal } from "astal/gtk3"
import { execAsync } from "astal/process"
import CalendarWidget from "./widgets/Calendar"
import AudioWidget from "./widgets/Audio"
import NetworkWidget from "./widgets/Network"
import SystemMonitorWidget from "./widgets/SystemMonitor"
import PowerDisplayWidget from "./widgets/PowerDisplay"
import MediaControlWidget from "./widgets/MediaControl"
import QuickSettingsWidget from "./widgets/QuickSettings"
import ProductivityWidget from "./widgets/Productivity"
import GamingWidget from "./widgets/Gaming"
import NotificationCenterWidget from "./widgets/NotificationCenter"
import PowerMenuWidget from "./widgets/PowerMenu"

// --- Popup state management ---
const popupStates: { [key: string]: boolean } = {};
const popupWindows: { [key: string]: Widget.Window | null } = {};

interface PopupPosition {
    x?: number;
    y?: number;
    anchor?: number;
    marginTop?: number;
    marginRight?: number;
    marginBottom?: number;
    marginLeft?: number;
    monitor?: number;
}

function getWaybarGeometry(): Promise<{ height: number; width: number; x: number; y: number }> {
    return execAsync(["bash", "-c", `
        # Get waybar window info using hyprctl
        hyprctl clients -j | jq -r '.[] | select(.class == "waybar") | "\\(.at[0]) \\(.at[1]) \\(.size[0]) \\(.size[1])"'
    `]).then(output => {
        const [x, y, width, height] = output.trim().split(' ').map(Number);
        return { x: x || 0, y: y || 0, width: width || 1920, height: height || 42 };
    }).catch(() => {
        // Fallback values based on your waybar config
        return { x: 16, y: 8, width: 1888, height: 42 }; // margin-left: 16, margin-top: 8, height: 42
    });
}

function getDisplayGeometry(): Promise<{ width: number; height: number }> {
    return execAsync(["bash", "-c", `
        hyprctl monitors -j | jq -r '.[0] | "\\(.width) \\(.height)"'
    `]).then(output => {
        const [width, height] = output.trim().split(' ').map(Number);
        return { width: width || 1920, height: height || 1080 };
    }).catch(() => {
        return { width: 1920, height: 1080 };
    });
}

async function calculatePopupPosition(popupType: string): Promise<PopupPosition> {
    const waybar = await getWaybarGeometry();
    const display = await getDisplayGeometry();
    
    const popupWidth = 380;  // Estimated popup width
    const popupHeight = 500; // Estimated popup height
    const padding = 10;
    
    // Calculate position below waybar, aligned to the right
    const x = display.width - popupWidth - padding - 16; // 16 is waybar margin-right
    const y = waybar.y + waybar.height + padding;
    
    print(`Calculated position for ${popupType}: x=${x}, y=${y}`);
    print(`Waybar: x=${waybar.x}, y=${waybar.y}, w=${waybar.width}, h=${waybar.height}`);
    print(`Display: w=${display.width}, h=${display.height}`);
    
    return {
        anchor: Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT,
        marginTop: y,
        marginRight: 20,
        monitor: 0
    };
}

function createPopup(name: string, WidgetComponent: any): void {
    if (popupWindows[name]) {
        print(`Popup ${name} already exists, skipping creation`);
        return;
    }
    
    print(`Creating popup: ${name}`);
    
    calculatePopupPosition(name).then(position => {
        popupWindows[name] = new Widget.Window({
            name: `${name}-popup`,
            className: "popup-window",
            visible: true,
            anchor: position.anchor,
            layer: Astal.Layer.OVERLAY,
            marginTop: position.marginTop,
            marginRight: position.marginRight,
            marginLeft: position.marginLeft,
            marginBottom: position.marginBottom,
            keymode: Astal.Keymode.ON_DEMAND,
            exclusivity: Astal.Exclusivity.NORMAL,
            monitor: position.monitor ?? 0,
            setup: (self: any) => {
                print(`Setting up popup window: ${name}`);
                
                // Escape key to close
                self.connect("key-press-event", (_: any, event: any) => {
                    const [, keyval] = event.get_keyval();
                    if (keyval === 65307) { // Escape key
                        print(`Escape pressed, closing ${name}`);
                        destroyPopup(name);
                        return true;
                    }
                    return false;
                });
                
                // Focus out to close (optional)
                // self.connect("focus-out-event", () => {
                //     print(`Focus lost, closing ${name}`);
                //     setTimeout(() => destroyPopup(name), 100); // Small delay to prevent immediate close
                //     return false;
                // });
                
                // Cleanup on destroy
                self.connect("destroy", () => {
                    print(`Popup ${name} destroyed`);
                    popupWindows[name] = null;
                    popupStates[name] = false;
                });
                
                // Force focus
                self.present();
                self.grab_focus();
            },
            child: new Widget.Box({
                className: "popup-content",
                child: WidgetComponent({ fullView: true })
            })
        });
        
        popupStates[name] = true;
        print(`Popup ${name} created successfully`);
    }).catch(error => {
        print(`Error calculating position for ${name}: ${error}`);
        // Fallback to simple positioning
        popupWindows[name] = new Widget.Window({
            name: `${name}-popup`,
            className: "popup-window",
            visible: true,
            anchor: Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT,
            layer: Astal.Layer.OVERLAY,
            marginTop: 60,
            marginRight: 20,
            keymode: Astal.Keymode.ON_DEMAND,
            exclusivity: Astal.Exclusivity.NORMAL,
            setup: (self: any) => {
                self.connect("key-press-event", (_: any, event: any) => {
                    const [, keyval] = event.get_keyval();
                    if (keyval === 65307) {
                        destroyPopup(name);
                        return true;
                    }
                    return false;
                });
                
                self.connect("destroy", () => {
                    popupWindows[name] = null;
                    popupStates[name] = false;
                });
                
                self.present();
                self.grab_focus();
            },
            child: new Widget.Box({
                className: "popup-content", 
                child: WidgetComponent({ fullView: true })
            })
        });
        
        popupStates[name] = true;
        print(`Popup ${name} created with fallback positioning`);
    });
}

function destroyPopup(name: string): void {
    if (popupWindows[name]) {
        print(`Destroying popup: ${name}`);
        popupWindows[name]?.destroy();
        popupWindows[name] = null;
        popupStates[name] = false;
    }
}

function togglePopup(name: string, WidgetComponent: any): void {
    print(`Toggling popup: ${name}, current state: ${popupStates[name]}`);
    
    if (popupStates[name] && popupWindows[name]) {
        destroyPopup(name);
    } else {
        // Close all other popups first
        Object.keys(popupWindows).forEach(key => {
            if (key !== name) destroyPopup(key);
        });
        createPopup(name, WidgetComponent);
    }
}

App.start({
    css: "./style.css",

    requestHandler(request: string, res: (response: any) => void) {
        const [action] = request.split(' ');
        print(`Received request: ${action}`);
        
        const widgetMap: Record<string, any> = {
            "toggle_calendar": CalendarWidget,
            "toggle_audio": AudioWidget,
            "toggle_network": NetworkWidget,
            "toggle_system": SystemMonitorWidget,
            "toggle_power_display": PowerDisplayWidget,
            "toggle_media_control": MediaControlWidget,
            "toggle_quick_settings": QuickSettingsWidget,
            "toggle_productivity": ProductivityWidget,
            "toggle_gaming": GamingWidget,
            "toggle_notifications": NotificationCenterWidget,
            "toggle_power_menu": PowerMenuWidget,
        };
        
        if (widgetMap[action]) {
            const key = action.replace("toggle_", "");
            togglePopup(key, widgetMap[action]);
            res({
                status: "success", 
                action: action,
                state: popupStates[key] ? 'shown' : 'hidden'
            });
        } else {
            print(`Unknown request: ${action}`);
            res({ 
                status: "error", 
                message: `Unknown request: ${action}` 
            });
        }
    },

    main() {
        print("AGS started - popups will be created on demand");
        
        // Test positioning calculation
        calculatePopupPosition("test").then(pos => {
            print(`Test positioning result: ${JSON.stringify(pos)}`);
        });
        
        return null; // No windows created at startup
    }
})
