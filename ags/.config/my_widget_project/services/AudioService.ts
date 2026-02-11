import { exec, execAsync } from "ags/process"

export interface AudioDevice {
  id: string
  name: string
  type: "sink" | "source"
  volume: number
  muted: boolean
}

export interface AudioApp {
  name: string
  volume: number
  muted: boolean
}

export class AudioService {
  private volumeLevel: number = 100
  private muteStatus: boolean = false
  private micMuteStatus: boolean = false
  private defaultSink: string = ""
  private defaultSource: string = ""
  private devices: AudioDevice[] = []
  private apps: AudioApp[] = []
  private initialized: boolean = false

  constructor() {
    // Don't initialize in constructor - lazy load on first access
    // This prevents blocking during startup
  }

  private ensureInitialized() {
    if (!this.initialized) {
      this.updateVolumeLevel()
      this.updateMuteStatus()
      this.initialized = true
    }
  }

  private updateVolumeLevel() {
    try {
      const output = exec(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
      if (output) {
        // wpctl outputs like: "Volume: 0.50" or "Volume: 0.50 [MUTED]"
        const match = output.match(/Volume:\s+(\d+\.?\d*)/)
        if (match) {
          // Convert from 0.0-1.0 scale to 0-100 scale
          this.volumeLevel = Math.round(parseFloat(match[1]) * 100)
        }
      }
    } catch (e) {
      // Silent fail - use default value
      this.volumeLevel = 100
    }
  }

  private updateMuteStatus() {
    try {
      const output = exec(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"])
      if (output) {
        this.muteStatus = output.includes("[MUTED]")
      }
    } catch (e) {
      this.muteStatus = false
    }

    try {
      const output = exec(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])
      if (output) {
        this.micMuteStatus = output.includes("[MUTED]")
      }
    } catch (e) {
      this.micMuteStatus = false
    }
  }

  private updateDevices() {
    try {
      const output = exec(["wpctl", "status"])
      if (output) {
        const lines = output.split("\n")
        // Parse wpctl status output to get devices
        // This is a simplified version - you might want to enhance it
      }
    } catch (e) {
      // Silent fail
    }
  }

  getVolume(): number {
    this.ensureInitialized()
    try {
      this.updateVolumeLevel()
    } catch (e) {
      // Keep previous value on error
    }
    return this.volumeLevel
  }

  setVolume(percentage: number) {
    const normalized = Math.max(0, Math.min(100, percentage)) / 100
    try {
      execAsync(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", normalized.toString()])
      this.volumeLevel = Math.round(normalized * 100)
    } catch (e) {
      // Silent fail
    }
  }

  isMuted(): boolean {
    this.ensureInitialized()
    try {
      this.updateMuteStatus()
    } catch (e) {
      // Keep previous value on error
    }
    return this.muteStatus
  }

  toggleMute() {
    try {
      execAsync(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
      this.muteStatus = !this.muteStatus
    } catch (e) {
      // Silent fail
    }
  }

  isMicMuted(): boolean {
    this.ensureInitialized()
    try {
      this.updateMuteStatus()
    } catch (e) {
      // Keep previous value on error
    }
    return this.micMuteStatus
  }

  toggleMicMute() {
    try {
      execAsync(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
      this.micMuteStatus = !this.micMuteStatus
    } catch (e) {
      // Silent fail
    }
  }

  getDevices(): AudioDevice[] {
    this.updateDevices()
    return this.devices
  }

  getApps(): AudioApp[] {
    try {
      const output = exec(["pactl", "list", "sink-inputs"])
      if (output) {
        const apps: AudioApp[] = []
        // Split by "Sink Input #" to get individual applications
        const appBlocks = output.split(/Sink Input #(\d+)/)
        
        for (let i = 1; i < appBlocks.length; i += 2) {
          const inputId = appBlocks[i]
          const block = appBlocks[i + 1]
          
          if (!block.trim()) continue
          
          // Extract application name
          const appMatch = block.match(/application\.name\s*=\s*"([^"]+)"/)
          const appName = appMatch ? appMatch[1] : "Unknown App"
          
          // Extract window/media title if available
          const mediaMatch = block.match(/media\.name\s*=\s*"([^"]+)"/)
          const mediaTitle = mediaMatch ? mediaMatch[1] : null
          
          // Extract volume percentage (pactl shows as "XXXX / YY%")
          const volMatch = block.match(/Volume:[^\n]*?(\d+)%/)
          const volume = volMatch ? parseInt(volMatch[1]) : 50
          
          // Check if muted
          const muted = block.includes("Mute: yes")
          
          // Create a unique identifier for this sink input
          const uniqueId = `${appName}_${inputId}_${mediaTitle || ''}`
          
          apps.push({
            name: mediaTitle ? `${appName} - ${mediaTitle.substring(0, 30)}` : appName,
            volume,
            muted
          })
        }
        
        this.apps = apps
      }
    } catch (e) {
      // Silent fail
      console.warn("Failed to parse apps:", e)
      this.apps = []
    }
    return this.apps
  }

  openAdvancedAudioManager() {
    try {
      execAsync(["pavucontrol"])
    } catch (e) {
      console.error("Failed to open pavucontrol:", e)
    }
  }

  // Get apps grouped by application name for expandable UI
  getGroupedApps(): { [key: string]: AudioApp[] } {
    const apps = this.getApps()
    const grouped: { [key: string]: AudioApp[] } = {}
    
    for (const app of apps) {
      // Get the base app name (before any " - " separator for window titles)
      const baseAppName = app.name.split(" - ")[0]
      
      if (!grouped[baseAppName]) {
        grouped[baseAppName] = []
      }
      grouped[baseAppName].push(app)
    }
    
    return grouped
  }
}

export const audioService = new AudioService()
