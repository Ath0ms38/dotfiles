// AGS v2 Gaming Widget

import { Variable, bind } from "astal"
import { execAsync } from "astal/process"

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

const gpuStats = Variable({ usage: 0, temp: 0, memory: 0 }).poll(2000, async () => {
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
        return <box className="gaming-full" vertical spacing={12}>
            <label className="widget-title" label="🎮 Gaming & Performance" />
            
            {/* Game Launchers */}
            <box className="launchers-section" vertical spacing={8}>
                <label className="section-label" label="Game Launchers" />
                <box className="launcher-grid" spacing={8}>
                    {gameLaunchers.map(launcher => (
                        <button key={launcher.name} className="launcher-button"
                            onClicked={() => execAsync([launcher.command])}>
                            <box vertical spacing={4}>
                                <icon icon={launcher.icon} iconSize={32} />
                                <label label={launcher.name} />
                            </box>
                        </button>
                    ))}
                </box>
            </box>

            {/* GPU Stats */}
            <box className="gpu-stats-section" vertical spacing={8}>
                <label className="section-label" label="GPU Performance" />
                <box vertical spacing={6}>
                    <box className="stat-row" spacing={12}>
                        <label label="Usage:" />
                        <box hexpand />
                        <label label={bind(gpuStats).as(stats => `${stats.usage}%`)} />
                    </box>
                    <progressbar value={bind(gpuStats).as(stats => stats.usage / 100)} />
                    
                    <box className="stat-row" spacing={12}>
                        <label label="Temperature:" />
                        <box hexpand />
                        <label label={bind(gpuStats).as(stats => `${stats.temp}°C`)} />
                    </box>
                    
                    <box className="stat-row" spacing={12}>
                        <label label="Memory:" />
                        <box hexpand />
                        <label label={bind(gpuStats).as(stats => `${stats.memory}%`)} />
                    </box>
                    <progressbar value={bind(gpuStats).as(stats => stats.memory / 100)} />
                </box>
            </box>

            {/* Gaming Mode */}
            <box className="gaming-mode-section" vertical spacing={8}>
                <label className="section-label" label="Gaming Mode" />
                <box spacing={12}>
                    <label label="Enable Gaming Mode" />
                    <box hexpand />
                    <switch active={bind(gameMode)}
                        onActivate={({ active }) => {
                            gameMode.set(active)
                            if (active) {
                                // Enable gaming optimizations
                                execAsync(["hyprctl", "keyword", "decoration:blur", "false"])
                                execAsync(["hyprctl", "keyword", "animations:enabled", "false"])
                                execAsync(["powerprofilesctl", "set", "performance"])
                                execAsync(["notify-send", "Gaming Mode", "Performance optimizations enabled"])
                            } else {
                                // Restore normal settings
                                execAsync(["hyprctl", "keyword", "decoration:blur", "true"])
                                execAsync(["hyprctl", "keyword", "animations:enabled", "true"])
                                execAsync(["powerprofilesctl", "set", "balanced"])
                                execAsync(["notify-send", "Gaming Mode", "Normal settings restored"])
                            }
                        }} />
                </box>
                <label className="gaming-mode-info" 
                    label="Disables visual effects and enables performance mode" />
            </box>

            {/* Quick Actions */}
            <box className="gaming-actions" spacing={6}>
                <button className="action-button" onClicked={() => execAsync(["mangohud", "glxgears"])}>
                    Test MangoHud
                </button>
                <button className="action-button" onClicked={() => execAsync(["corectrl"])}>
                    CoreCtrl
                </button>
                <button className="action-button" onClicked={() => execAsync(["nvidia-settings"])}>
                    NVIDIA Settings
                </button>
            </box>
        </box>
    }

    return <box className="gaming-compact">
        <icon icon="input-gaming-symbolic" />
    </box>
}