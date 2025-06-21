import { App, Widget } from "astal/gtk3"
import CalendarWidget from "./Calendar"

App.start({
  main() {
    return new Widget.Window({
      name: "calendar-test",
      anchor: ["top", "right"],
      child: CalendarWidget({ fullView: true })
    })
  }
})