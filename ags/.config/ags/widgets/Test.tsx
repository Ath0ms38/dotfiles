import { Widget } from "astal/gtk3"

export default function TestWidget({ fullView = false }: { fullView?: boolean }) {
    if (fullView) {
        return Widget.Box({
            className: "test-widget-full",
            vertical: true,
            spacing: 12,
            children: [
                Widget.Label({
                    className: "widget-title",
                    label: "🧪 Test Widget"
                }),
                Widget.Button({
                    label: "Click Me",
                    onClicked: () => console.log("Button clicked!")
                }),
                Widget.Label({
                    label: "If you see this, AGS is working!"
                })
            ]
        })
    }
    
    return Widget.Box({
        className: "test-widget-compact",
        children: [Widget.Label({ label: "Test" })]
    })
}