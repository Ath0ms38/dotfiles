// ags/.config/ags/widgets/Gaming.tsx

import { Variable, bind } from "astal"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

interface GameLauncher {
    name: string
    command: string
    icon: string
}

const gameLaunchers: GameLauncher[] = [
    { name: "Steam", command: "steam", icon: "steam" },
    { name: "Lutris", command: "lutris", icon: "lutris" },
    { name: "Heroic", command: "heroic", icon: "heroic" },
    { name: "Bottles", command: "bottles", icon: "bottles" },
    { name: "Minecraft", command: "minecraft-launcher", icon: "minecraft" }
]

const gpuStats = Variable({ usage: 0, temp: 0, memory: 0 }).poll(5000, async () => {
    const usage = await execAsync(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"])
        .then(out => parseInt(out)).catch(() => 0)
    
    const temp = await execAsync(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"])
        .then(out => parseInt(out)).catch(() => 0)
    
    const memory = await execAsync(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"])
        .then(out => {
            const [used, total] = out.split(',').map(v => parseInt(v))
            return Math.round((used / total) * 100)
        }).catch(() => 0)
    
    return { usage, temp, memory }
})

const gameMode = Variable(false)

export default function GamingWidget({ fullView = false }: { fullView?: boolean }) {
    if (fullView) {
        return new Widget.Box({
            className: "gaming-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "🎮 Gaming & Performance"
                }),
                
                // Game Launchers
                new Widget.Box({
                    className: "launchers-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Game Launchers"
                        }),
                        new Widget.Box({
                            className: "launcher-grid",
                            spacing: 8,
                            children: gameLaunchers.map(launcher => new Widget.Button({
                                className: "launcher-button",
                                onClicked: () => execAsync([launcher.command]),
                                child: new Widget.Box({
                                    vertical: true,
                                    spacing: 4,
                                    children: [
                                        new Widget.Icon({ icon: launcher.icon, iconSize: 32 }),
                                        new Widget.Label({ label: launcher.name })
                                    ]
                                })
                            }))
                        })
                    ]
                }),

                // GPU Stats
                new Widget.Box({
                    className: "gpu-stats-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "GPU Performance"
                        }),
                        new Widget.Box({
                            vertical: true,
                            spacing: 6,
                            children: [
                                new Widget.Box({
                                    className: "stat-row",
                                    spacing: 12,
                                    children: [
                                        new Widget.Label({ label: "Usage:" }),
                                        new Widget.Box({ hexpand: true }),
                                        new Widget.Label({
                                            label: bind(gpuStats).as(stats => `${stats.usage}%`)
                                        })
                                    ]
                                }),
                                new Widget.LevelBar({
                                    value: bind(gpuStats).as(stats => stats.usage / 100),
                                    minValue: 0,
                                    maxValue: 1
                                }),
                                
                                new Widget.Box({
                                    className: "stat-row",
                                    spacing: 12,
                                    children: [
                                        new Widget.Label({ label: "Temperature:" }),
                                        new Widget.Box({ hexpand: true }),
                                        new Widget.Label({
                                            label: bind(gpuStats).as(stats => `${stats.temp}°C`)
                                        })
                                    ]
                                }),
                                
                                new Widget.Box({
                                    className: "stat-row",
                                    spacing: 12,
                                    children: [
                                        new Widget.Label({ label: "Memory:" }),
                                        new Widget.Box({ hexpand: true }),
                                        new Widget.Label({
                                            label: bind(gpuStats).as(stats => `${stats.memory}%`)
                                        })
                                    ]
                                }),
                                new Widget.LevelBar({
                                    value: bind(gpuStats).as(stats => stats.memory / 100),
                                    minValue: 0,
                                    maxValue: 1
                                })
                            ]
                        })
                    ]
                }),

                // Gaming Mode
                new Widget.Box({
                    className: "gaming-mode-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Gaming Mode"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                new Widget.Label({ label: "Enable Gaming Mode" }),
                                new Widget.Box({ hexpand: true }),
                                // @ts-ignore - Switch widget
                                new Widget.Switch({
                                    active: bind(gameMode),
                                    onActivate: ({ active }: any) => {
                                        gameMode.set(active)
                                        if (active) {
                                            execAsync(["hyprctl", "keyword", "decoration:blur", "false"])
                                            execAsync(["hyprctl", "keyword", "animations:enabled", "false"])
                                            execAsync(["powerprofilesctl", "set", "performance"])
                                            execAsync(["notify-send", "Gaming Mode", "Performance optimizations enabled"])
                                        } else {
                                            execAsync(["hyprctl", "keyword", "decoration:blur", "true"])
                                            execAsync(["hyprctl", "keyword", "animations:enabled", "true"])
                                            execAsync(["powerprofilesctl", "set", "balanced"])
                                            execAsync(["notify-send", "Gaming Mode", "Normal settings restored"])
                                        }
                                    }
                                })
                            ]
                        }),
                        new Widget.Label({
                            className: "gaming-mode-info",
                            label: "Disables visual effects and enables performance mode"
                        })
                    ]
                }),

                // Quick Actions
                new Widget.Box({
                    className: "gaming-actions",
                    spacing: 6,
                    children: [
                        new Widget.Button({
                            className: "action-button",
                            label: "Test MangoHud",
                            onClicked: () => execAsync(["mangohud", "glxgears"])
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "CoreCtrl",
                            onClicked: () => execAsync(["corectrl"])
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "NVIDIA Settings",
                            onClicked: () => execAsync(["nvidia-settings"])
                        })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "gaming-compact",
        children: [new Widget.Icon({ icon: "input-gaming-symbolic" })]
    })
}
