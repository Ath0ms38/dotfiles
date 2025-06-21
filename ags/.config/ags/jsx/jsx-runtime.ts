import { Gtk } from "astal/gtk3"

export function jsx(tag: any, props: any) {
    // Debug: log the tag type
    // Remove or comment out after debugging
    // @ts-ignore
    if (typeof globalThis !== "undefined" && globalThis.console) {
        // eslint-disable-next-line no-console
        console.log("JSX tag type:", typeof tag, "tag:", tag && tag.name ? tag.name : tag);
    }
    if (typeof tag === "function") {
        return tag(props ?? {});
    }
    return Gtk.Widget({
        type: tag,
        ...props
    });
}

export { jsx as jsxs }
export { jsx as jsxDEV }