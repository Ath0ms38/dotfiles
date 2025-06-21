// Minimal standalone test for NetworkWidget
import { App, Widget } from "astal/gtk3"
import NetworkWidget from "./Network"

App.start({
    main() {
        return new Widget.Window({
            name: "network-test",
            anchor: ["top", "right"],
            child: NetworkWidget({ fullView: true })
        })
    }
})