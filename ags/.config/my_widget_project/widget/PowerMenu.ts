import Gtk from "gi://Gtk?version=4.0"
import Astal from "gi://Astal?version=4.0"
import Gdk from "gi://Gdk?version=4.0"

export function PowerMenuWidget() {
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
      label: "⏻ Power Menu",
    })
  )

  const buttonBox = new Gtk.Box({
    orientation: Gtk.Orientation.HORIZONTAL,
    spacing: 8,
  })

  buttonBox.append(
    new Gtk.Button({
      label: "Sleep",
    })
  )

  buttonBox.append(
    new Gtk.Button({
      label: "Restart",
    })
  )

  buttonBox.append(
    new Gtk.Button({
      label: "Shutdown",
    })
  )

  box.append(buttonBox)

  const window = new Astal.Window({
    name: "power_menu",
    visible: false,
    namespace: "power_menu",
    cssClasses: ["PowerMenuWidget"],
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
