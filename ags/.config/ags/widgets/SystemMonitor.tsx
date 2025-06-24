// ags/.config/ags/widgets/SystemMonitor.tsx

import { Variable, bind } from "astal"
import { execAsync } from "astal/process"
import { Widget } from "astal/gtk3"

interface SystemInfo {
    cpuUsage: number
    cpuTemp: number
    memUsage: number
    memTotal: number
    memUsed: number
    diskUsage: number
    diskTotal: number
    diskUsed: number
    gpuUsage: number
    gpuTemp: number
}

const systemInfo = Variable<SystemInfo>({
    cpuUsage: 0,
    cpuTemp: 0,
    memUsage: 0,
    memTotal: 0,
    memUsed: 0,
    diskUsage: 0,
    diskTotal: 0,
    diskUsed: 0,
    gpuUsage: 0,
    gpuTemp: 0
}).poll(5000, async () => {
    const cpu = await execAsync(["bash", "-c", "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"])
        .then(out => parseInt(out)).catch(() => 0)
    
    const cpuTemp = await execAsync(["bash", "-c", "sensors | grep 'Package id 0:' | awk '{print $4}' | sed 's/+//g' | sed 's/°C//g'"])
        .then(out => parseInt(out)).catch(() => 0)
    
    const memInfo = await execAsync(["bash", "-c", "free -b | grep '^Mem:'"])
        .then(out => {
            const parts = out.split(/\s+/)
            const total = parseInt(parts[1])
            const used = parseInt(parts[2])
            return { total, used, percent: Math.round((used / total) * 100) }
        }).catch(() => ({ total: 0, used: 0, percent: 0 }))
    
    const diskInfo = await execAsync(["bash", "-c", "df -B1 / | tail -1"])
        .then(out => {
            const parts = out.split(/\s+/)
            const total = parseInt(parts[1])
            const used = parseInt(parts[2])
            return { total, used, percent: parseInt(parts[4]) }
        }).catch(() => ({ total: 0, used: 0, percent: 0 }))
    
    const gpuUsage = await execAsync(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"])
        .then(out => parseInt(out)).catch(() => 0)
    
    const gpuTemp = await execAsync(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"])
        .then(out => parseInt(out)).catch(() => 0)
    
    return {
        cpuUsage: cpu,
        cpuTemp: cpuTemp,
        memUsage: memInfo.percent,
        memTotal: memInfo.total,
        memUsed: memInfo.used,
        diskUsage: diskInfo.percent,
        diskTotal: diskInfo.total,
        diskUsed: diskInfo.used,
        gpuUsage: gpuUsage,
        gpuTemp: gpuTemp
    }
})

export default function SystemMonitorWidget({ fullView = false }: { fullView?: boolean }) {
    if (fullView) {
        return new Widget.Box({
            className: "system-monitor-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "💻 System Monitor"
                }),
                
                // CPU Section
                new Widget.Box({
                    className: "cpu-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "CPU"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                // @ts-ignore - CircularProgress widget
                                new Widget.CircularProgress({
                                    className: "usage-circle",
                                    value: bind(systemInfo).as(info => info.cpuUsage / 100)
                                }),
                                new Widget.Box({
                                    vertical: true,
                                    children: [
                                        new Widget.Label({
                                            label: bind(systemInfo).as(info => `${info.cpuUsage}% Usage`)
                                        }),
                                        new Widget.Label({
                                            className: "temp-label",
                                            label: bind(systemInfo).as(info => `${info.cpuTemp}°C`)
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                }),

                // Memory Section
                new Widget.Box({
                    className: "memory-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Memory"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                // @ts-ignore - CircularProgress widget
                                new Widget.CircularProgress({
                                    className: "usage-circle",
                                    value: bind(systemInfo).as(info => info.memUsage / 100)
                                }),
                                new Widget.Box({
                                    vertical: true,
                                    children: [
                                        new Widget.Label({
                                            label: bind(systemInfo).as(info => `${info.memUsage}% Usage`)
                                        }),
                                        new Widget.Label({
                                            className: "usage-details",
                                            label: bind(systemInfo).as(info => 
                                                `${(info.memUsed / 1024**3).toFixed(1)} / ${(info.memTotal / 1024**3).toFixed(1)} GB`
                                            )
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                }),

                // Disk Section
                new Widget.Box({
                    className: "disk-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Disk (/)"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                // @ts-ignore - CircularProgress widget
                                new Widget.CircularProgress({
                                    className: "usage-circle",
                                    value: bind(systemInfo).as(info => info.diskUsage / 100)
                                }),
                                new Widget.Box({
                                    vertical: true,
                                    children: [
                                        new Widget.Label({
                                            label: bind(systemInfo).as(info => `${info.diskUsage}% Usage`)
                                        }),
                                        new Widget.Label({
                                            className: "usage-details",
                                            label: bind(systemInfo).as(info => 
                                                `${(info.diskUsed / 1024**3).toFixed(0)} / ${(info.diskTotal / 1024**3).toFixed(0)} GB`
                                            )
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                }),

                // GPU Section
                new Widget.Box({
                    className: "gpu-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "GPU (NVIDIA)"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                // @ts-ignore - CircularProgress widget
                                new Widget.CircularProgress({
                                    className: "usage-circle",
                                    value: bind(systemInfo).as(info => info.gpuUsage / 100)
                                }),
                                new Widget.Box({
                                    vertical: true,
                                    children: [
                                        new Widget.Label({
                                            label: bind(systemInfo).as(info => `${info.gpuUsage}% Usage`)
                                        }),
                                        new Widget.Label({
                                            className: "temp-label",
                                            label: bind(systemInfo).as(info => `${info.gpuTemp}°C`)
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                }),

                // Quick actions
                new Widget.Box({
                    className: "system-actions",
                    spacing: 6,
                    children: [
                        new Widget.Button({
                            className: "action-button",
                            label: "Btop",
                            onClicked: () => execAsync(["kitty", "-e", "btop"])
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "Htop",
                            onClicked: () => execAsync(["kitty", "-e", "htop"])
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
        className: "system-monitor-compact",
        children: [new Widget.Icon({ icon: "computer-symbolic" })]
    })
}
