"""
VPN Widget
One popup, two pages behind a tab bar:
- Proton: status, one-click disconnect, feature presets, searchable countries
- WireGuard: the NetworkManager tunnels, one row each, click to toggle

The Proton tab is dropped entirely when the CLI is not installed, and the tab
bar hides itself when only one page is left.
"""

from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.stack import Stack
from fabric.widgets.entry import Entry
from gi.repository import GLib

from .base_popup import BasePopup, popup_manager
from services.vpn import ProtonVpn
from services.wireguard import WireGuard, Tunnel


# Presets that do not need the country list, so they work even signed out.
PRESETS = [
    ("󰓅", "Fastest", "Fastest available server", []),
    ("󰇧", "P2P", "Fastest P2P-optimised server", ["--p2p"]),
    ("󰦝", "Secure Core", "Route through a hardened entry country", ["--securecore"]),
    ("󰖟", "Tor", "Exit through the Tor network", ["--tor"]),
    ("󰒝", "Random", "Random available server", ["--random"]),
]

# The scrolled lists must not v-expand: inside a layer-shell window that is
# still negotiating its size, an expanding child swallows the whole allocation
# and the header/presets/search never get painted.
LIST_HEIGHT = 260
POPUP_WIDTH = 380

STATUS_CLASSES = ("connected", "connecting", "disconnecting", "error")


def _apply_state_class(widget, state: str):
    for cls in STATUS_CLASSES:
        widget.remove_style_class(cls)
    if state in STATUS_CLASSES:
        widget.add_style_class(state)


class CountryRow(Button):
    """One country in the Proton list; click connects to its fastest server."""

    def __init__(self, name: str, code: str, on_pick, **kwargs):
        self.country_name = name
        self.country_code = code

        super().__init__(
            name="vpn-country-row",
            on_clicked=lambda *_: on_pick(code),
            tooltip_text=f"Connect to the fastest server in {name}",
            child=CenterBox(
                start_children=[Label(label=name, h_align="start")],
                end_children=[Label(label=code, name="vpn-country-code")],
            ),
            **kwargs,
        )

    def matches(self, needle: str) -> bool:
        return needle in self.country_name.lower() or needle in self.country_code.lower()


class TunnelRow(Button):
    """One WireGuard tunnel; click brings it up or takes it down."""

    STATE_LABELS = {
        "connected": "on",
        "connecting": "…",
        "disconnecting": "…",
        "disconnected": "off",
    }

    def __init__(self, tunnel: Tunnel, on_toggle, **kwargs):
        self.tunnel = tunnel

        self.state_label = Label(
            label=self.STATE_LABELS.get(tunnel.state, tunnel.state),
            name="vpn-tunnel-state",
        )
        _apply_state_class(self.state_label, tunnel.state)

        subtitle = tunnel.address or tunnel.interface
        if tunnel.external:
            subtitle = "started outside NetworkManager"

        super().__init__(
            name="vpn-tunnel-row",
            on_clicked=lambda *_: on_toggle(tunnel),
            child=CenterBox(
                start_children=[
                    Box(
                        orientation="v",
                        spacing=1,
                        children=[
                            Label(label=tunnel.name, h_align="start"),
                            Label(
                                label=subtitle,
                                name="vpn-tunnel-subtitle",
                                h_align="start",
                            ),
                        ],
                    )
                ],
                end_children=[self.state_label],
            ),
            **kwargs,
        )

        if tunnel.external:
            # Nothing to activate: NM only assumed the device, it has no
            # profile to bring back once the tunnel goes down.
            self.set_sensitive(False)
            self.set_tooltip_text(
                f"{tunnel.name} was brought up with wg-quick.\n"
                "Import it into NetworkManager to control it from here."
            )
        elif tunnel.is_up:
            self.set_tooltip_text(f"Take {tunnel.name} down")
        else:
            self.set_tooltip_text(f"Bring {tunnel.name} up")


class ProtonPage(Box):
    """Proton VPN page: status, presets and the searchable country list."""

    def __init__(self, service: ProtonVpn, on_action, **kwargs):
        self.service = service
        self.on_action = on_action
        self._rows = []

        self.status_label = Label(label="…", name="vpn-status", h_align="start")
        self.speed_label = Label(label="", name="vpn-speed", h_align="start")

        self.disconnect_button = Button(
            label="Disconnect",
            name="vpn-disconnect",
            h_expand=True,
            on_clicked=lambda *_: self.service.disconnect_vpn(),
        )

        header = Box(
            name="vpn-header",
            orientation="v",
            spacing=2,
            children=[
                Label(
                    label="󰦝 ProtonVPN",
                    name="vpn-title",
                    h_align="start",
                ),
                self.status_label,
                self.speed_label,
            ],
        )

        preset_box = Box(orientation="h", spacing=6, name="vpn-presets")
        for icon, label, tooltip, args in PRESETS:
            preset_box.add(
                Button(
                    name="vpn-preset",
                    label=f"{icon}\n{label}",
                    tooltip_text=tooltip,
                    on_clicked=lambda _, a=args: self._connect_preset(a),
                )
            )

        self.search_entry = Entry(
            placeholder="Search country…",
            name="vpn-search",
            h_expand=True,
            on_changed=lambda *_: self._apply_filter(),
        )

        self.country_list_box = Box(orientation="v", spacing=2, name="vpn-country-list")

        self.countries_status = Label(
            label="",
            name="vpn-countries-status",
            h_align="start",
            line_wrap="word",
        )

        scrolled = ScrolledWindow(
            name="vpn-country-scroll",
            child=self.country_list_box,
            h_expand=True,
            min_content_size=(POPUP_WIDTH - 40, LIST_HEIGHT),
            max_content_size=(POPUP_WIDTH - 40, LIST_HEIGHT),
        )
        scrolled.set_size_request(POPUP_WIDTH - 40, LIST_HEIGHT)

        super().__init__(
            orientation="v",
            spacing=10,
            name="vpn-proton-page",
            children=[
                header,
                self.disconnect_button,
                preset_box,
                self.search_entry,
                self.countries_status,
                scrolled,
            ],
            **kwargs,
        )

        self.service.connect("changed", lambda *_: self._update_status())
        self.service.connect("countries-changed", lambda *_: self._rebuild_countries())
        self.service.connect("bandwidth-changed", lambda *_: self._update_speed())

        self._update_status()
        self._rebuild_countries()

    # -- actions -----------------------------------------------------------

    def _connect_preset(self, args):
        self.service.connect_with_args(args)
        self.on_action()

    def _connect_country(self, code):
        self.service.connect_vpn(country=code)
        self.on_action()

    def _signin(self):
        self.service.open_signin()
        self.on_action()

    # -- state -------------------------------------------------------------

    def on_open(self):
        """Refresh the country list in the background when the page shows."""
        self.service.refresh_countries()
        self.search_entry.set_text("")

    def focus_search(self):
        self.search_entry.grab_focus()

    def _update_status(self):
        state = self.service.state
        server = self.service.server

        text = {
            "connected": f"Connected — {server}" if server else "Connected",
            "connecting": "Connecting…",
            "disconnecting": "Disconnecting…",
            "error": self.service.message,
            "disconnected": "Not connected",
        }.get(state, state)

        self.status_label.set_label(text)
        _apply_state_class(self.status_label, state)

        self.disconnect_button.set_sensitive(state in ("connected", "connecting"))
        self._update_speed()

    def _update_speed(self):
        connected = self.service.state == "connected"
        self.speed_label.set_label(self.service.bandwidth if connected else "")
        self.speed_label.set_visible(connected)

    def _rebuild_countries(self):
        for child in self.country_list_box.get_children():
            self.country_list_box.remove(child)
        self._rows = []

        countries = self.service.countries

        if not countries:
            error = self.service.countries_error
            if "sign in" in error.lower() or "authentication" in error.lower():
                self.countries_status.set_label(
                    "Sign in to load the country list — the presets above still work."
                )
                self.country_list_box.add(
                    Button(
                        label="Sign in to Proton VPN",
                        name="vpn-signin",
                        on_clicked=lambda *_: self._signin(),
                    )
                )
            else:
                self.countries_status.set_label(error or "Loading countries…")
            self.country_list_box.show_all()
            return

        self.countries_status.set_label("")
        for name, code in countries:
            row = CountryRow(name, code, self._connect_country)
            self._rows.append(row)
            self.country_list_box.add(row)

        self.country_list_box.show_all()
        self._apply_filter()

    def _apply_filter(self):
        needle = self.search_entry.get_text().strip().lower()
        for row in self._rows:
            row.set_visible(not needle or row.matches(needle))


class WireGuardPage(Box):
    """WireGuard page: the NetworkManager tunnels, one togglable row each."""

    IMPORT_HINT = (
        "No WireGuard profile in NetworkManager.\n"
        "Import a config once with:\n"
        "nmcli connection import type wireguard file /etc/wireguard/<name>.conf"
    )

    def __init__(self, service: WireGuard, **kwargs):
        self.service = service

        self.status_label = Label(label="…", name="vpn-status", h_align="start")
        self.speed_label = Label(label="", name="vpn-speed", h_align="start")

        header = Box(
            name="vpn-header",
            orientation="v",
            spacing=2,
            children=[
                Label(
                    label="󰖂 WireGuard",
                    name="vpn-title",
                    h_align="start",
                ),
                self.status_label,
                self.speed_label,
            ],
        )

        self.tunnel_list_box = Box(orientation="v", spacing=4, name="vpn-tunnel-list")

        self.tunnels_status = Label(
            label="",
            name="vpn-countries-status",
            h_align="start",
            line_wrap="word",
        )

        scrolled = ScrolledWindow(
            name="vpn-tunnel-scroll",
            child=self.tunnel_list_box,
            h_expand=True,
            min_content_size=(POPUP_WIDTH - 40, LIST_HEIGHT),
            max_content_size=(POPUP_WIDTH - 40, LIST_HEIGHT),
        )
        scrolled.set_size_request(POPUP_WIDTH - 40, LIST_HEIGHT)

        super().__init__(
            orientation="v",
            spacing=10,
            name="vpn-wireguard-page",
            children=[header, self.tunnels_status, scrolled],
            **kwargs,
        )

        self.service.connect("changed", lambda *_: self._rebuild())
        self.service.connect("bandwidth-changed", lambda *_: self._update_speed())

        self._rebuild()

    def on_open(self):
        self._rebuild()

    def _rebuild(self):
        for child in self.tunnel_list_box.get_children():
            self.tunnel_list_box.remove(child)

        tunnels = self.service.tunnels
        for tunnel in tunnels:
            self.tunnel_list_box.add(TunnelRow(tunnel, self.service.toggle))
        self.tunnel_list_box.show_all()

        self.tunnels_status.set_label("" if tunnels else self.IMPORT_HINT)
        self._update_status()

    def _update_status(self):
        state = self.service.state
        name = self.service.active_name

        text = {
            "connected": f"Up — {name}" if name else "Up",
            "connecting": "Bringing up…",
            "disconnecting": "Taking down…",
            "disconnected": "No tunnel up",
        }.get(state, state)

        if self.service.message:
            text = self.service.message
            state = "error"

        self.status_label.set_label(text)
        _apply_state_class(self.status_label, state)
        self._update_speed()

    def _update_speed(self):
        connected = self.service.state == "connected"
        self.speed_label.set_label(self.service.bandwidth if connected else "")
        self.speed_label.set_visible(connected)


class VpnWidget(BasePopup):
    """VPN control popup with a Proton page and a WireGuard page.

    Opens and closes with ax-shell's notch animation. That animation is not the
    Revealer — the notch keeps its revealer open permanently — it is a Stack in
    crossfade with interpolate_size, morphing its height between the two pages
    while the CSS bounce curve runs on the card. So the popup gets the same
    thing: a Stack that morphs between an empty page and the content, driven
    identically in both directions, with BasePopup's revealer left open and
    inert underneath.
    """

    POPUP_WIDTH = POPUP_WIDTH

    # ax-notch's own numbers: 200ms on the stack crossfade, 250ms on the CSS
    # transition of the card. The window is hidden only once the slower of the
    # two has finished, otherwise the bounce is cut off mid-curve.
    MORPH_MS = 200
    SETTLE_MS = 250

    # The search entry must accept typing (and Escape must dismiss) as soon as
    # the menu opens, without a click inside it first.
    KEYBOARD_MODE_WHEN_OPEN = "exclusive"

    def __init__(self, proton: ProtonVpn | None, wireguard: WireGuard, **kwargs):
        self.proton = proton
        self.wireguard = wireguard
        self.proton_page = None
        self.wireguard_page = None
        self._tabs = {}

        super().__init__(
            name="vpn-widget",
            anchor="top right",
            margin="8px 20px 0px 0px",
            width=self.POPUP_WIDTH,
            **kwargs,
        )

        # The morph Stack is the animation now, so the revealer must not add a
        # second one: leave it open with no transition of its own. Its
        # notify::child-revealed handler then never fires, which is why open and
        # close below drive the window's visibility themselves.
        self.revealer.set_transition_duration(0)
        self.revealer.set_reveal_child(True)

    def build_content(self):
        pages = []

        if self.proton is not None:
            self.proton_page = ProtonPage(self.proton, self.close)
            pages.append(("proton", "󰦝 Proton", self.proton_page))

        self.wireguard_page = WireGuardPage(self.wireguard)
        pages.append(("wireguard", "󰖂 WireGuard", self.wireguard_page))

        # Left homogeneous (GTK's default) on purpose: the popup then keeps the
        # height of the tallest page, so switching tabs does not renegotiate the
        # layer surface and make the window jump.
        self.stack = Stack(
            name="vpn-pages",
            transition_type="crossfade",
            transition_duration=150,
        )
        for key, _label, page in pages:
            self.stack.add_named(page, key)

        self.tab_bar = Box(orientation="h", spacing=6, name="vpn-tabs", h_expand=True)
        for key, label, _page in pages:
            tab = Button(
                name="vpn-tab",
                label=label,
                h_expand=True,
                on_clicked=lambda _, k=key: self.show_page(k),
            )
            self._tabs[key] = tab
            self.tab_bar.add(tab)

        # A single page needs no switcher.
        self.tab_bar.set_visible(len(pages) > 1)
        self.tab_bar.set_no_show_all(len(pages) < 2)

        self.show_page(pages[0][0])

        content = Box(
            orientation="v",
            spacing=10,
            name="vpn-content",
            children=[self.tab_bar, self.stack],
        )

        # The page the popup morphs out of. Zero height, but the shared popup
        # frame (2px border + 14px padding) keeps the layer surface around 32px
        # even here, well clear of the 1px collapse that empty popups fall into.
        collapsed = Box(name="vpn-collapsed")
        collapsed.set_size_request(self.POPUP_WIDTH, 0)

        self.morph = Stack(
            name="vpn-morph",
            transition_type="crossfade",
            transition_duration=self.MORPH_MS,
        )
        # Non-homogeneous is what makes the morph a morph: a homogeneous Stack
        # sizes to its largest child, so the collapsed page would already be
        # full height and nothing would animate.
        self.morph.set_homogeneous(False)
        self.morph.set_interpolate_size(True)
        self.morph.add_named(collapsed, "collapsed")
        self.morph.add_named(content, "content")
        self.morph.set_visible_child_name("collapsed")

        return self.morph

    def show_page(self, key: str):
        self.stack.set_visible_child_name(key)
        for name, tab in self._tabs.items():
            if name == key:
                tab.add_style_class("active")
            else:
                tab.remove_style_class("active")

        page = self.stack.get_visible_child()
        if page is not None and self._is_open:
            page.on_open()
        if page is self.proton_page:
            GLib.idle_add(page.focus_search)

    def on_open(self):
        """Refresh whichever page is showing."""
        page = self.stack.get_visible_child()
        if page is not None:
            page.on_open()
        if page is self.proton_page:
            # Runs before the window is mapped, so defer the focus grab.
            GLib.idle_add(page.focus_search)

    # -- open / close ------------------------------------------------------
    #
    # BasePopup drives its revealer and hides on notify::child-revealed. Here
    # the morph Stack is the animation, so both directions are handled by hand
    # and stay symmetric: same widget, same curve, same duration each way.

    def open(self):
        if self._is_open:
            return

        self._is_open = True
        popup_manager.register_popup(self)
        self.on_open()

        # Take keyboard focus before mapping so Escape reaches the window
        self.set_keyboard_mode(self.KEYBOARD_MODE_WHEN_OPEN)

        self.morph.set_visible_child_name("collapsed")
        self.show_all()
        self.content_box.add_style_class("open")

        # Switching in the same frame as the map gives GTK no previous size to
        # interpolate from, and the stack snaps to full height instead.
        GLib.idle_add(self._morph_to_content)

    def _morph_to_content(self):
        if self._is_open:
            self.morph.set_visible_child_name("content")
        return False

    def close(self):
        if not self._is_open:
            return

        self._is_open = False
        self.on_close()
        self.set_keyboard_mode("none")

        self.content_box.remove_style_class("open")
        self.morph.set_visible_child_name("collapsed")

        GLib.timeout_add(self.SETTLE_MS, self._finish_close)

    def _finish_close(self):
        # Reopened while shrinking: the new open owns the window now.
        if not self._is_open:
            self.hide()
            popup_manager.unregister_popup(self)
        return False

    def close_immediate(self):
        """Drop the window with no animation (another popup is taking over)."""
        self._is_open = False
        self.set_keyboard_mode("none")
        self.content_box.remove_style_class("open")
        self.morph.set_visible_child_name("collapsed")
        self.hide()
        popup_manager.unregister_popup(self)
