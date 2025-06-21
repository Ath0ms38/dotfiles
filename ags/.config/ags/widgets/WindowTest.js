#!/usr/bin/env -S ags run

const { App, Widget } = imports.gi['astal/gtk3'];

App.start({
    windows: [
        Widget.Window({
            name: "window-test",
            anchor: ["top", "right"],
            child: Widget.Box({
                className: "window-test-widget",
                vertical: true,
                spacing: 16,
                children: [
                    Widget.Label({
                        label: "This is a direct window test widget (JS)!"
                    }),
                    Widget.Button({
                        label: "Close",
                        onClicked: () => App.quit()
                    })
                ]
            })
        })
    ]
});