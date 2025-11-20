import Gtk from "gi://Gtk?version=4.0"
import Astal from "gi://Astal?version=4.0"
import Gdk from "gi://Gdk?version=4.0"

export function NotificationCenterWidget() {
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
      label: "🔔 Notification Center",
    })
  )

  box.append(
    new Gtk.Label({
      label: "You have 3 new notifications",
    })
  )

  box.append(
    new Gtk.Button({
      label: "Clear All",
    })
  )

  const scrolledWindow = new Gtk.ScrolledWindow()
  scrolledWindow.child = box
  scrolledWindow.set_max_content_height(300)

  const window = new Astal.Window({
    name: "notifications",
    visible: false,
    namespace: "notifications",
    cssClasses: ["NotificationCenterWidget"],
    keymode: Astal.Keymode.ON_DEMAND,
    anchor: Astal.WindowAnchor.TOP | Astal.WindowAnchor.RIGHT,
    layer: Astal.Layer.OVERLAY,
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
