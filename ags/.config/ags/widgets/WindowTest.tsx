#!/usr/bin/env -S ags run

import { App, Widget } from "astal/gtk3"

App.start({
    main() {
        return new Widget.Window({
            name: "window-test",
            anchor: ["top", "right"],
            child: new Widget.Box({
                className: "window-test-widget",
                vertical: true,
                spacing: 16,
                children: [
                    new Widget.Label({
                        label: "This is a direct window test widget!"
                    }),
                    new Widget.Button({
                        label: "Close",
                        onClicked: () => App.quit()
                    })
                ]
            })
        });
    }
})