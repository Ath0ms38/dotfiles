import Gtk from "gi://Gtk?version=4.0"
import Astal from "gi://Astal?version=4.0"
import Gdk from "gi://Gdk?version=4.0"
import { audioService } from "../services/AudioService"
import { createState } from "ags"
import { createPoll } from "ags/time"

export function AudioWidget() {
  // Initialize with safe default values
  let initialVolume = 100
  let initialMuted = false
  let initialMicMuted = false

  try {
    initialVolume = audioService.getVolume()
    initialMuted = audioService.isMuted()
    initialMicMuted = audioService.isMicMuted()
  } catch (e) {
    // Use defaults if initialization fails
    console.warn("Audio service initialization failed, using defaults")
  }

  const [volume, setVolume] = createState(initialVolume)
  const [isMuted, setIsMuted] = createState(initialMuted)
  const [isMicMuted, setIsMicMuted] = createState(initialMicMuted)

  // Poll for volume updates every 1000ms
  const volumePoll = createPoll(initialVolume, 1000, (prev) => {
    try {
      const current = audioService.getVolume()
      if (current !== prev) {
        setVolume(current)
      }
      return current
    } catch (e) {
      return prev
    }
  })

  // Create a scrollable container for the entire widget
  const scrolledWindow = new Gtk.ScrolledWindow()
  scrolledWindow.set_max_content_height(600)
  scrolledWindow.set_min_content_width(350)
  scrolledWindow.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
  scrolledWindow.set_propagate_natural_height(false)
  scrolledWindow.set_propagate_natural_width(false)

  const mainBox = new Gtk.Box({
    orientation: Gtk.Orientation.VERTICAL,
    spacing: 12,
    marginTop: 12,
    marginBottom: 12,
    marginStart: 12,
    marginEnd: 12,
    widthRequest: 350,
  })

  // Title
  mainBox.append(
    new Gtk.Label({
      label: "🔊 Audio Control",
      cssClasses: ["title"],
    })
  )

  // Master Volume Control
  const volumeBox = new Gtk.Box({
    orientation: Gtk.Orientation.HORIZONTAL,
    spacing: 12,
    homogeneous: false,
  })

  const volumeLabel = new Gtk.Label({
    label: "Speaker:",
    widthRequest: 80,
    xalign: 0,
  })
  volumeBox.append(volumeLabel)

  const volumeSlider = new Gtk.Scale({
    orientation: Gtk.Orientation.HORIZONTAL,
    adjustment: new Gtk.Adjustment({
      value: initialVolume,
      lower: 0,
      upper: 150,
      stepIncrement: 1,
      pageIncrement: 5,
      pageSize: 0,
    }),
    drawValue: true,
    valuePos: Gtk.PositionType.RIGHT,
    widthRequest: 200,
    hexpand: true,
  })

  // Connect volume state to slider updates
  const handleVolumeChange = () => {
    const currentVol = audioService.getVolume()
    volumeSlider.get_adjustment().set_value(currentVol)
  }

  volumeSlider.connect("value-changed", () => {
    try {
      const val = volumeSlider.get_adjustment().get_value()
      audioService.setVolume(val)
      setVolume(val)
    } catch (e) {
      console.warn("Failed to set volume:", e)
    }
  })

  volumeBox.append(volumeSlider)
  mainBox.append(volumeBox)

  // Mute/Unmute button
  const muteButton = new Gtk.Button({
    label: initialMuted ? "🔇 Unmute" : "🔊 Mute",
    cssClasses: ["audio-button"],
  })

  muteButton.connect("clicked", () => {
    try {
      audioService.toggleMute()
      const muted = audioService.isMuted()
      setIsMuted(muted)
      muteButton.set_label(muted ? "🔇 Unmute" : "🔊 Mute")
    } catch (e) {
      console.warn("Failed to toggle mute:", e)
    }
  })

  mainBox.append(muteButton)

  // Microphone Control
  const micBox = new Gtk.Box({
    orientation: Gtk.Orientation.HORIZONTAL,
    spacing: 12,
    homogeneous: false,
  })

  const micLabel = new Gtk.Label({
    label: "Microphone:",
    widthRequest: 80,
    xalign: 0,
  })
  micBox.append(micLabel)

  const micButton = new Gtk.Button({
    label: initialMicMuted ? "🎤 Muted" : "🎙️ Active",
    cssClasses: ["audio-button"],
    hexpand: true,
  })

  micButton.connect("clicked", () => {
    try {
      audioService.toggleMicMute()
      const micMuted = audioService.isMicMuted()
      setIsMicMuted(micMuted)
      micButton.set_label(micMuted ? "🎤 Muted" : "🎙️ Active")
    } catch (e) {
      console.warn("Failed to toggle mic mute:", e)
    }
  })

  micBox.append(micButton)
  mainBox.append(micBox)

  // Separator
  mainBox.append(
    new Gtk.Separator({
      orientation: Gtk.Orientation.HORIZONTAL,
    })
  )

  // Application volume manager button
  const appManagerButton = new Gtk.Button({
    label: "📱 App Volume Manager",
    cssClasses: ["audio-button"],
  })

  appManagerButton.connect("clicked", () => {
    try {
      audioService.openAdvancedAudioManager()
    } catch (e) {
      console.warn("Failed to open audio manager:", e)
    }
  })

  mainBox.append(appManagerButton)

  scrolledWindow.set_child(mainBox)

  // Periodic sync of volume slider to show current system volume
  const volumeSyncInterval = setInterval(() => {
    try {
      const currentVol = audioService.getVolume()
      const sliderVal = volumeSlider.get_adjustment().get_value()
      // Only update if there's a significant difference (user isn't actively dragging)
      if (Math.abs(currentVol - sliderVal) > 2) {
        volumeSlider.get_adjustment().set_value(currentVol)
      }
    } catch (e) {
      // Silent fail
    }
  }, 1000)

  const window = new Astal.Window({
    name: "audio",
    visible: false,
    namespace: "audio",
    cssClasses: ["AudioWidget"],
    keymode: Astal.Keymode.ON_DEMAND,
    anchor: Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT,
    layer: Astal.Layer.OVERLAY,
    widthRequest: 380,
    heightRequest: 320,
    child: scrolledWindow,
  })

  // Add keyboard event controller
  const keyController = new Gtk.EventControllerKey()
  keyController.connect("key-pressed", (_self, keyval) => {
    if (keyval === Gdk.KEY_Escape) {
      window.visible = false
      return true
    }
    return false
  })
  window.add_controller(keyController)

  return window
}
