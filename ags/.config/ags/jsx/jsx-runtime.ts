import { Gtk } from "astal/gtk3"

export function jsx(tag: any, props: any) {
    return Gtk.Widget({
        type: tag,
        ...props
    })
}

export { jsx as jsxs }
export { jsx as jsxDEV }