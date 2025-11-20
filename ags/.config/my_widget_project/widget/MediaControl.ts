import Gtk from "gi://Gtk?version=4.0"
import Astal from "gi://Astal?version=4.0"
import Gdk from "gi://Gdk?version=4.0"

export function MediaControlWidget() {
  const box = new Gtk.Box({
    orientation: Gtk.Orientation.VERTICAL,
    spacing: 12,
    marginTop: 12,
    marginBottom: 12,
    marginStart: 12,
    marginEnd: 12,
  })

  box.append(
    new Gtk.Label({
      label: "🎵 Media Control",
    })
  )

  box.append(
    new Gtk.Label({
      label: "Now Playing: Artist - Song",
    })
  )

  const controlBox = new Gtk.Box({
    orientation: Gtk.Orientation.HORIZONTAL,
    spacing: 8,
  })

  controlBox.append(
    new Gtk.Button({
      label: "⏮",
    })
  )

  controlBox.append(
    new Gtk.Button({
      label: "⏯",
    })
  )

  controlBox.append(
    new Gtk.Button({
      label: "⏭",
    })
  )

  box.append(controlBox)

  const window = new Astal.Window({
    name: "media_control",
    visible: false,
    namespace: "media_control",
    cssClasses: ["MediaControlWidget"],
    keymode: Astal.Keymode.ON_DEMAND,
    anchor: Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT,
    layer: Astal.Layer.OVERLAY,
    child: box,
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
