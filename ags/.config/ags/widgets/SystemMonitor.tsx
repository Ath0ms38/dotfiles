// AGS v2 System Monitor Widget

import { Variable, bind } from "astal"
import { execAsync } from "astal/process"
import Gtk from "gi://Gtk?version=3.0"

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
        return <box className="system-monitor-full" vertical spacing={12}>
            <label className="widget-title" label="💻 System Monitor" />
            
            {/* CPU Section */}
            <box className="cpu-section" vertical spacing={8}>
                <label className="section-label" label="CPU" />
                <box spacing={12}>
                    <circularprogress className="usage-circle"
                        value={bind(systemInfo).as(info => info.cpuUsage / 100)} />
                    <box vertical>
                        <label label={bind(systemInfo).as(info => `${info.cpuUsage}% Usage`)} />
                        <label className="temp-label" 
                            label={bind(systemInfo).as(info => `${info.cpuTemp}°C`)} />
                    </box>
                </box>
            </box>

            {/* Memory Section */}
            <box className="memory-section" vertical spacing={8}>
                <label className="section-label" label="Memory" />
                <box spacing={12}>
                    <circularprogress className="usage-circle"
                        value={bind(systemInfo).as(info => info.memUsage / 100)} />
                    <box vertical>
                        <label label={bind(systemInfo).as(info => `${info.memUsage}% Usage`)} />
                        <label className="usage-details" 
                            label={bind(systemInfo).as(info => 
                                `${(info.memUsed / 1024**3).toFixed(1)} / ${(info.memTotal / 1024**3).toFixed(1)} GB`
                            )} />
                    </box>
                </box>
            </box>

            {/* Disk Section */}
            <box className="disk-section" vertical spacing={8}>
                <label className="section-label" label="Disk (/)" />
                <box spacing={12}>
                    <circularprogress className="usage-circle"
                        value={bind(systemInfo).as(info => info.diskUsage / 100)} />
                    <box vertical>
                        <label label={bind(systemInfo).as(info => `${info.diskUsage}% Usage`)} />
                        <label className="usage-details" 
                            label={bind(systemInfo).as(info => 
                                `${(info.diskUsed / 1024**3).toFixed(0)} / ${(info.diskTotal / 1024**3).toFixed(0)} GB`
                            )} />
                    </box>
                </box>
            </box>

            {/* GPU Section */}
            <box className="gpu-section" vertical spacing={8}>
                <label className="section-label" label="GPU (NVIDIA)" />
                <box spacing={12}>
                    <circularprogress className="usage-circle"
                        value={bind(systemInfo).as(info => info.gpuUsage / 100)} />
                    <box vertical>
                        <label label={bind(systemInfo).as(info => `${info.gpuUsage}% Usage`)} />
                        <label className="temp-label" 
                            label={bind(systemInfo).as(info => `${info.gpuTemp}°C`)} />
                    </box>
                </box>
            </box>

            {/* Quick actions */}
            <box className="system-actions" spacing={6}>
                <button className="action-button" onClicked={() => execAsync(["kitty", "-e", "btop"])}>
                    Btop
                </button>
                <button className="action-button" onClicked={() => execAsync(["kitty", "-e", "htop"])}>
                    Htop
                </button>
                <button className="action-button" onClicked={() => execAsync(["nvidia-settings"])}>
                    NVIDIA Settings
                </button>
            </box>
        </box>
    }

    return <box className="system-monitor-compact">
        <icon icon="computer-symbolic" />
    </box>
}