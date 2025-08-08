// ags/.config/ags/widgets/Audio.tsx

import { bind, Variable } from "astal"
import { Widget } from "astal/gtk3"
import { execAsync } from "astal/process"
import Wp from "gi://AstalWp"
import GLib from "gi://GLib"

export default function AudioWidget({ fullView = false }: { fullView?: boolean }) {
    const audio = Wp.get_default()
    const speaker = audio?.audio?.defaultSpeaker
    const mic = audio?.audio?.defaultMicrophone

    // Fast path known sink ids (adjust to your hardware)
    const KNOWN_SPEAKER_IDS = ["60"]
    const KNOWN_HEADPHONE_IDS = ["92"]

    function setDefaultSink(kind: "speaker" | "headphones") {
        const knownIds = kind === "speaker" ? KNOWN_SPEAKER_IDS : KNOWN_HEADPHONE_IDS
        execAsync([
            "bash",
            "-lc",
            `for id in ${knownIds.join(" ")}; do if wpctl status | sed -n '/Sinks:/,/Sources:/p' | grep -q "[[:space:]]$id\\."; then wpctl set-default "$id" && echo "[audio-widget] set-default (fast) ${kind} -> $id" >&2 && exit 0; fi; done; exit 22`,
        ])
            .then(() => { /* fast path success */ })
            .catch(() => {
                const keywords = kind === "speaker"
                    ? ["speaker"]
                    : ["headphone", "headphones", "razer", "bluetooth", "bt", "barracuda"]
                const kw = keywords.join(",")
                execAsync([
                    "bash",
                    "-lc",
                    `id=$(wpctl status | sed -n '/Sinks:/,/Sources:/p' | awk -v kw="${kw}" 'BEGIN{IGNORECASE=1; n=split(kw,a,",")} /[0-9]+\\./ { low=tolower($0); for(i=1;i<=n;i++){ if(index(low,a[i])>0){ if (match($0, /[0-9]+\\./)) { id=substr($0,RSTART,RLENGTH-1); print id; exit } } } }'); if [ -n "$id" ]; then wpctl set-default "$id" && echo "[audio-widget] set-default (scan) ${kind} -> $id" >&2; else echo "[audio-widget] no sink matched keywords (${kind})" >&2; fi`,
                ]).catch(console.error)
            })
    }

    // -------- Per-application (stream) volume management (restored simple version) --------
    interface StreamInfo { id: string; name: string; volume: number }
    const perAppShown = Variable(false)
    const streamsVar = Variable<StreamInfo[]>([])
    const perAppPhase = Variable<"closed" | "loading" | "ready">("closed")

    function refreshStreams() {
        perAppPhase.set("loading")
        execAsync([
            "bash",
            "-lc",
            `ids=$(wpctl status | sed -n '/Streams:/,/^Video/p' | awk '/^[[:space:]]+[0-9]+\\./{gsub("\\\\.","",$1); print $1}');
hyprjson=""
if command -v hyprctl >/dev/null 2>&1; then
  hyprjson=$(hyprctl clients -j 2>/dev/null | tr -d '\\n')
fi
for id in $ids; do
  insp=$(wpctl inspect "$id" 2>/dev/null) || continue
  echo "$insp" | grep -q 'media.class = "Stream/Output/Audio"' || continue

  app=$(echo "$insp"   | sed -n 's/ *\\* application.name = "\\(.*\\)"/\\1/p'      | head -n1)
  media=$(echo "$insp" | sed -n 's/ *\\* media.name = "\\(.*\\)"/\\1/p'            | head -n1)
  desc=$(echo "$insp"  | sed -n 's/ *\\* node.description = "\\(.*\\)"/\\1/p'      | head -n1)
  pid=$(echo "$insp"   | sed -n 's/ *application.process.id = "\\(.*\\)"/\\1/p'    | head -n1)

  name="$media"
  [ -z "$name" ] && name="$app"
  [ -z "$name" ] && name="$desc"
  [ -z "$name" ] && name="Stream $id"

  if [ -n "$pid" ] && [ -n "$hyprjson" ]; then
    wtitle=$(printf '%s\n' "$hyprjson" | awk -v pid="$pid" 'BEGIN{RS="{";FS="\""} $0~("pid\":"pid){ for(i=1;i<=NF;i++){ if($i=="title" && (i+2)<=NF){ print $(i+2); exit } } }' | head -n1)
    if [ -n "$wtitle" ]; then
      name="$wtitle"
    fi
  fi

  name=$(echo "$name" | sed -E 's/:playback_[A-Z]{2}//g' | tr '|' ' ')
  vol=$(wpctl get-volume "$id" 2>/dev/null | grep -Eo '[0-9]+\\.[0-9]+' | head -n1)
  [ -z "$vol" ] && vol=0.0
  echo "$id|$name|$media|$desc|$vol"
done`
        ]).then(out => {
            const lines = out.trim().split("\n").filter(Boolean)
            const seen = new Set<string>()
            const streams: StreamInfo[] = lines
                .filter(l => l.includes("|"))
                .map(l => {
                    const parts = l.split("|")
                    // legacy fallback (old 3-field format)
                    let id = parts[0]
                    let rawName = parts[1] || ""
                    let mediaName = parts[2] || ""
                    let descName = parts[3] || ""
                    let volStr = parts[parts.length - 1] || "0"
                    const lnameAll = (rawName + " " + mediaName + " " + descName).toLowerCase()

                    if (lnameAll.includes("playback_fl") || lnameAll.includes("playback_fr")) return null
                    if (lnameAll.includes("player") && lnameAll.includes("playback")) return null

                    // Build a richer display name:
                    let name = rawName

                    // Prefer mediaName if rawName is too generic
                    const generic = ["firefox", "chromium", "brave-browser", "google chrome", "brave", "vlc"]
                    if (generic.includes(rawName.toLowerCase()) && mediaName && mediaName.length > 2) {
                        name = mediaName
                    }

                    // If descName is longer and contains extra info, prefer it
                    if (descName && descName.length > name.length && !descName.toLowerCase().includes("pipewire")) {
                        name = descName
                    }

                    // Combine if distinct and short
                    if (mediaName && mediaName !== name && mediaName.length > 6 && !name.toLowerCase().includes(mediaName.toLowerCase())) {
                        // Avoid duplication if desc already included
                        name = `${name} — ${mediaName}`
                    }

                    // Clean stray duplicate separators
                    name = name.replace(/( — ){2,}/g, " — ").trim()

                    if (seen.has(id)) return null
                    seen.add(id)
                    return { id, name, volume: parseFloat(volStr) || 0 }
                })
                .filter((x): x is StreamInfo => !!x)
            streamsVar.set(streams)
            if (perAppShown.get()) perAppPhase.set("ready")
            else perAppPhase.set("closed")
        }).catch(e => {
            console.error(e)
            perAppPhase.set("ready")
        })
    }

    function streamRow(stream: StreamInfo) {
        const volVar = Variable(stream.volume)
        return new Widget.Box({
            className: "app-volume-row",
            spacing: 6,
            children: [
                new Widget.Label({
                    className: "app-volume-name",
                    hexpand: true,
                    halign: "START",
                    label: stream.name,
                }),
                new Widget.Slider({
                    className: "app-volume-slider",
                    drawValue: false,
                    min: 0,
                    max: 1,
                    value: bind(volVar),
                    widthRequest: 110,
                    onDragged: ({ value }: any) => {
                        volVar.set(value)
                        execAsync(["wpctl", "set-volume", stream.id, value.toFixed(3)])
                            .catch(console.error)
                    },
                }),
                new Widget.Label({
                    className: "app-volume-percent",
                    label: bind(volVar).as(v => `${Math.round(v * 100)}%`),
                    halign: "END",
                }),
            ],
        })
    }

    const perAppList = new Widget.Box({
        vertical: true,
        spacing: 6,
        className: bind(perAppPhase).as(p => {
            if (p === "loading") return "per-app-volume-list loading"
            if (p === "ready") return "per-app-volume-list ready"
            return "per-app-volume-list"
        }),
        children: [
            new Widget.Box({
                spacing: 6,
                className: "per-app-actions",
                children: [
                    new Widget.Button({
                        className: "per-app-refresh",
                        label: "Refresh",
                        onClicked: () => refreshStreams(),
                    }),
                ],
            }),
            new Widget.Box({
                vertical: true,
                spacing: 4,
                children: bind(streamsVar).as(streams =>
                    streams.length
                        ? streams.map(s => streamRow(s))
                        : [new Widget.Label({
                            className: "no-streams-label",
                            label: perAppPhase.get() === "loading" ? "Loading..." : "No active audio streams",
                            halign: "START",
                        })]
                ),
            }),
        ],
    })

    // Use crossfade to avoid vertical height animation that stretches outer border
    const perAppRevealer = new (Widget as any).Revealer({
        transition: "crossfade",
        transitionDuration: 140,
        revealChild: bind(perAppShown),
        child: perAppList,
    })

    const perAppSection = new Widget.Box({
        className: "per-app-section",
        vertical: true,
        spacing: 4,
        children: [
            new Widget.Button({
                className: "per-app-toggle",
                label: bind(perAppShown).as(s => s ? "▲ Hide App Volumes" : "▼ Show App Volumes"),
                onClicked: () => {
                    const open = perAppShown.get()
                    if (open) {
                        perAppShown.set(false)
                        perAppPhase.set("closed")
                    } else {
                        perAppShown.set(true)
                        if (streamsVar.get().length === 0) {
                            refreshStreams()
                        } else {
                            perAppPhase.set("ready")
                        }
                    }
                },
            }),
            perAppRevealer,
        ],
    })
    // ------------------------------------------------------------

    if (!audio) {
        return new Widget.Box({
            className: "audio-widget-error",
            vertical: true,
            children: [
                new Widget.Label({ label: "Audio service not available" })
            ]
        })
    }

    if (fullView) {
        return new Widget.Box({
            className: "audio-widget-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "🎵 Audio Control"
                }),

                // Speaker section
                speaker ? new Widget.Box({
                    className: "speaker-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Speaker"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                new Widget.Button({
                                    className: "mute-button",
                                    onClicked: () => speaker?.set_mute(!speaker.mute),
                                    child: new Widget.Icon({
                                        icon: bind(speaker, "volumeIcon").as(i => i || "audio-volume-medium-symbolic")
                                    })
                                }),
                                new Widget.Slider({
                                    className: "volume-slider",
                                    drawValue: false,
                                    hexpand: true,
                                    min: 0,
                                    max: 1,
                                    value: bind(speaker, "volume").as(v => v || 0),
                                    onDragged: ({ value }: any) => {
                                        if (speaker) speaker.volume = value
                                    }
                                }),
                                new Widget.Label({
                                    className: "volume-label",
                                    label: bind(speaker, "volume").as(v => `${Math.round((v || 0) * 100)}%`)
                                })
                            ]
                        })
                    ]
                }) : new Widget.Box({}),

                // Microphone section
                mic ? new Widget.Box({
                    className: "mic-section",
                    vertical: true,
                    spacing: 8,
                    children: [
                        new Widget.Label({
                            className: "section-label",
                            label: "Microphone"
                        }),
                        new Widget.Box({
                            spacing: 12,
                            children: [
                                new Widget.Button({
                                    className: "mute-button",
                                    onClicked: () => mic?.set_mute(!mic.mute),
                                    child: new Widget.Icon({
                                        icon: bind(mic, "volumeIcon").as(i => i || "microphone-sensitivity-medium-symbolic")
                                    })
                                }),
                                new Widget.Slider({
                                    className: "volume-slider",
                                    drawValue: false,
                                    hexpand: true,
                                    min: 0,
                                    max: 1,
                                    value: bind(mic, "volume").as(v => v || 0),
                                    onDragged: ({ value }: any) => {
                                        if (mic) mic.volume = value
                                    }
                                }),
                                new Widget.Label({
                                    className: "volume-label",
                                    label: bind(mic, "volume").as(v => `${Math.round((v || 0) * 100)}%`)
                                })
                            ]
                        })
                    ]
                }) : new Widget.Box({}),

                // Quick actions
                new Widget.Box({
                    className: "audio-actions",
                    spacing: 6,
                    children: [
                        new Widget.Button({
                            className: "action-button",
                            label: "Speakers",
                            onClicked: () => setDefaultSink("speaker"),
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "Headphones",
                            onClicked: () => setDefaultSink("headphones"),
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "Audio Settings",
                            onClicked: () => execAsync(["pavucontrol"]).catch(console.error)
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "EasyEffects",
                            onClicked: () => execAsync(["easyeffects"]).catch(console.error)
                        })
                    ]
                }),
                perAppSection
            ]
        })
    }

    return new Widget.Box({
        className: "audio-widget-compact",
        children: [
            new Widget.Icon({
                icon: speaker ? bind(speaker, "volumeIcon").as(i => i || "audio-volume-medium-symbolic") : "audio-volume-medium-symbolic"
            })
        ]
    })
}
