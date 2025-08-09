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

    // Track current default sink kind for highlighting buttons
    const currentSinkKind = Variable<"speaker" | "headphones" | "unknown">("unknown")

    function detectCurrentSink() {
        execAsync([
            "bash",
            "-lc",
            `wpctl status | sed -n '/Sinks:/,/Sources:/p' | awk '/\\*/{ if (match($0,/([0-9]+)\\./,m)) print m[1]; }'`,
        ])
            .then(id => {
                const sid = id.trim()
                if (sid.length === 0) {
                    currentSinkKind.set("unknown")
                    return
                }
                if (KNOWN_SPEAKER_IDS.includes(sid)) {
                    currentSinkKind.set("speaker")
                } else if (KNOWN_HEADPHONE_IDS.includes(sid)) {
                    currentSinkKind.set("headphones")
                } else {
                    // fallback lightweight keyword classification
                    execAsync([
                        "bash",
                        "-lc",
                        `wpctl status | sed -n '/Sinks:/,/Sources:/p' | awk '/\\*/{print tolower($0)}'`,
                    ])
                        .then(line => {
                            const l = line.toLowerCase()
                            if (/(headphone|bluetooth|bt|razer|barracuda)/.test(l)) currentSinkKind.set("headphones")
                            else if (/speaker/.test(l)) currentSinkKind.set("speaker")
                            else currentSinkKind.set("unknown")
                        })
                        .catch(() => currentSinkKind.set("unknown"))
                }
            })
            .catch(() => currentSinkKind.set("unknown"))
        return true
    }

    // initial detection
    detectCurrentSink()
    // periodic re-detect
    GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 3, () => {
        detectCurrentSink()
        return true
    })

    function setDefaultSink(kind: "speaker" | "headphones") {
        const knownIds = kind === "speaker" ? KNOWN_SPEAKER_IDS : KNOWN_HEADPHONE_IDS
        execAsync([
            "bash",
            "-lc",
            `for id in ${knownIds.join(" ")}; do if wpctl status | sed -n '/Sinks:/,/Sources:/p' | grep -q "[[:space:]]$id\\."; then wpctl set-default "$id" && echo "[audio-widget] set-default (fast) ${kind} -> $id" >&2 && exit 0; fi; done; exit 22`,
        ])
            .then(() => {
                GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 1, () => {
                    detectCurrentSink()
                    return GLib.SOURCE_REMOVE
                })
            })
            .catch(() => {
                const keywords = kind === "speaker"
                    ? ["speaker"]
                    : ["headphone", "headphones", "razer", "bluetooth", "bt", "barracuda"]
                const kw = keywords.join(",")
                execAsync([
                    "bash",
                    "-lc",
                    `id=$(wpctl status | sed -n '/Sinks:/,/Sources:/p' | awk -v kw="${kw}" 'BEGIN{IGNORECASE=1; n=split(kw,a,",")} /[0-9]+\\./ { low=tolower($0); for(i=1;i<=n;i++){ if(index(low,a[i])>0){ if (match($0, /[0-9]+\\./)) { id=substr($0,RSTART,RLENGTH-1); print id; exit } } } }'); if [ -n "$id" ]; then wpctl set-default "$id" && echo "[audio-widget] set-default (scan) ${kind} -> $id" >&2; else echo "[audio-widget] no sink matched keywords (${kind})" >&2; fi`,
                ])
                    .then(() => {
                        GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 1, () => {
                            detectCurrentSink()
                            return GLib.SOURCE_REMOVE
                        })
                    })
                    .catch(console.error)
            })
    }

    // -------- Per-application (stream) volume management --------
    interface StreamInfo {
        id: string
        rawApp: string
        title: string
        mediaName: string
        descName: string
        volume: number
        muted: boolean
        category: string
    }
    const perAppShown = Variable(false)
    const streamsVar = Variable<StreamInfo[]>([])
    const perAppPhase = Variable<"closed" | "loading" | "ready">("closed")
    // Track expanded/collapsed state per category
    const catExpanded: Record<string, any> = {}

    function refreshStreams() {
        perAppPhase.set("loading")
        execAsync([
            "bash",
            "-lc",
            `ids=$(wpctl status | sed -n '/Streams:/,/^Video/p' | awk '/^[[:space:]]+[0-9]+\\./{gsub("\\\\.","",$1); print $1}');
hyprjson="$(command -v hyprctl >/dev/null 2>&1 && hyprctl clients -j 2>/dev/null || echo "")"

for id in $ids; do
  insp=$(wpctl inspect "$id" 2>/dev/null) || continue
  echo "$insp" | grep -q 'media.class = "Stream/Output/Audio"' || continue

  app=$(echo "$insp"   | sed -n 's/ *\\* application.name = "\\(.*\\)"/\\1/p'      | head -n1)
  media=$(echo "$insp" | sed -n 's/ *\\* media.name = "\\(.*\\)"/\\1/p'            | head -n1)
  desc=$(echo "$insp"  | sed -n 's/ *\\* node.description = "\\(.*\\)"/\\1/p'      | head -n1)
  pid=$(echo "$insp"   | sed -n 's/ *application.process.id = "\\(.*\\)"/\\1/p'    | head -n1)

  wtitle=""
  if [ -n "$pid" ] && [ -n "$hyprjson" ]; then
    # Prefer jq for robust JSON parsing; fallback to awk if jq missing
    if command -v jq >/dev/null 2>&1; then
      wtitle=$(printf '%s\n' "$hyprjson" | jq -r --arg pid "$pid" '.[] | select(.pid==($pid|tonumber)) | .title' | head -n1)
    else
      wtitle=$(printf '%s\n' "$hyprjson" | awk -v pid="$pid" '
        /"pid":/ {
          if (match($0, /"pid": *([0-9]+)/, m) && m[1]==pid) inblk=1
        }
        inblk && /"title":/ {
          if (match($0, /"title": *"([^"]*)"/, t)) { print t[1]; exit }
        }')
    fi
  fi

  # Determine window title candidate priority: wtitle > media > desc > app > Stream id
  title="$wtitle"
  [ -z "$title" ] && title="$media"
  [ -z "$title" ] && title="$desc"
  [ -z "$title" ] && title="$app"
  [ -z "$title" ] && title="Stream $id"

  # cleanup
  title=$(echo "$title" | sed -E 's/:playback_[A-Z]{2}//g' | tr '|' ' ')
  app_clean=$(echo "$app" | tr '|' ' ')

  vol_line=$(wpctl get-volume "$id" 2>/dev/null)
  vol=$(echo "$vol_line" | grep -Eo '[0-9]+\\.[0-9]+' | head -n1)
  [ -z "$vol" ] && vol=0.0

  echo "$id|$app_clean|$title|$media|$desc|$vol|$(echo "$vol_line" | grep -q 'MUTED' && echo 1 || echo 0)"
done`
        ]).then(out => {
            const lines = out.trim().split("\n").filter(Boolean)
            interface Interim {
                id: string
                rawApp: string
                title: string
                mediaName: string
                descName: string
                volume: number
                muted: boolean
            }
            const interim: Interim[] = []
            const seen = new Set<string>()
            lines.forEach(l => {
                if (!l.includes("|")) return
                const parts = l.split("|")
                if (parts.length < 7) return
                const [id, rawApp, title, mediaName, descName, volStr, mutedStr] = parts
                if (!id || seen.has(id)) return

                interim.push({
                    id,
                    rawApp: rawApp || "Unknown",
                    title: title || rawApp || "Window",
                    mediaName,
                    descName,
                    volume: parseFloat(volStr) || 0,
                    muted: mutedStr.trim() === "1",
                })
                seen.add(id)
            })

            // Build final streams with category grouping (category = rawApp capitalized)
            const streams: StreamInfo[] = interim.map(s => {
                const base = s.rawApp || "Autre"
                const category = base.charAt(0).toUpperCase() + base.slice(1)
                return {
                    ...s,
                    category,
                }
            })
            streamsVar.set(streams)
            if (perAppShown.get()) perAppPhase.set("ready")
            else perAppPhase.set("closed")
        }).catch(e => {
            console.error(e)
            perAppPhase.set("ready")
        })
    }

    function moveStream(streamId: string, kind: "speaker" | "headphones") {
        const knownIds = kind === "speaker" ? KNOWN_SPEAKER_IDS : KNOWN_HEADPHONE_IDS
        execAsync([
            "bash",
            "-lc",
            `for sid in ${knownIds.join(" ")}; do if wpctl status | sed -n '/Sinks:/,/Sources:/p' | grep -q "[[:space:]]$sid\\."; then wpctl move ${streamId} $sid && echo "[audio-widget] moved stream ${streamId} -> ${kind}($sid)" >&2 && exit 0; fi; done;`,
        ])
            .then(() => {
                GLib.timeout_add(GLib.PRIORITY_DEFAULT, 150, () => {
                    refreshStreams()
                    return GLib.SOURCE_REMOVE
                })
            })
            .catch(console.error)
    }

    function streamRow(stream: StreamInfo) {
        const volVar = Variable(stream.volume)
        const mutedVar = Variable(stream.muted)
        const expanded = Variable(false)

        function applyVolume(value: number) {
            volVar.set(value)
            execAsync(["wpctl", "set-volume", stream.id, value.toFixed(3)]).catch(console.error)
        }

        function toggleMute() {
            execAsync(["wpctl", "set-mute", stream.id, mutedVar.get() ? "0" : "1"])
                .then(() => {
                    GLib.timeout_add(GLib.PRIORITY_DEFAULT, 120, () => {
                        refreshStreams()
                        return GLib.SOURCE_REMOVE
                    })
                })
                .catch(console.error)
        }

        const details = new (Widget as any).Revealer({
            transition: "crossfade",
            revealChild: bind(expanded),
            child: new Widget.Box({
                vertical: true,
                className: "stream-row-details",
                spacing: 6,
                children: [
                    new Widget.Slider({
                        className: "app-volume-slider",
                        drawValue: false,
                        hexpand: true,
                        min: 0,
                        max: 1,
                        value: bind(volVar),
                        onDragged: ({ value }: any) => applyVolume(value),
                    }),
                    new Widget.Box({
                        className: "app-stream-actions",
                        spacing: 6,
                        children: [
                            new Widget.Button({
                                className: "app-stream-action",
                                label: bind(mutedVar).as(m => m ? "Unmute" : "Mute"),
                                onClicked: () => toggleMute(),
                            }),
                            new Widget.Button({
                                className: "app-stream-action",
                                label: "→ Speakers",
                                onClicked: () => moveStream(stream.id, "speaker"),
                            }),
                            new Widget.Button({
                                className: "app-stream-action",
                                label: "→ Headphones",
                                onClicked: () => moveStream(stream.id, "headphones"),
                            }),
                            new Widget.Button({
                                className: "app-stream-action",
                                label: "Refresh",
                                onClicked: () => refreshStreams(),
                            }),
                        ],
                    }),
                ],
            }),
        })

        const header = new Widget.Box({
            className: "app-volume-row",
            spacing: 6,
            children: [
                new Widget.Button({
                    className: "dropdown-toggle",
                    onClicked: () => expanded.set(!expanded.get()),
                    label: bind(expanded).as(e => e ? "▲" : "▼"),
                }),
                new Widget.Label({
                    className: "app-volume-name",
                    hexpand: true,
                    halign: "START",
                    label: stream.title,
                }),
                new Widget.Label({
                    className: "app-volume-percent",
                    label: bind(volVar).as(v => `${Math.round(v * 100)}%`),
                    halign: "END",
                }),
            ],
        })

        return new Widget.Box({
            vertical: true,
            spacing: 2,
            children: [
                header,
                details,
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
                children: bind(streamsVar).as(streams => {
                    if (!streams.length) {
                        return [new Widget.Label({
                            className: "no-streams-label",
                            label: perAppPhase.get() === "loading" ? "Loading..." : "No active audio streams",
                            halign: "START",
                        })]
                    }
                    const groups: Record<string, StreamInfo[]> = {}
                    streams.forEach(s => {
                        groups[s.category] = groups[s.category] || []
                        groups[s.category].push(s)
                    })
                    const orderedCats = Object.keys(groups).sort()
                    const nodes: any[] = []
                    orderedCats.forEach(cat => {
                        if (!catExpanded[cat]) {
                            catExpanded[cat] = Variable(true)
                        }
                        const expandedVar = catExpanded[cat]
                        const header = new Widget.Box({
                            className: "app-category-header",
                            spacing: 6,
                            children: [
                                new Widget.Button({
                                    className: "category-toggle",
                                    onClicked: () => expandedVar.set(!expandedVar.get()),
                                    label: bind(expandedVar).as(e => e ? "▼" : "►"),
                                }),
                                new Widget.Label({
                                    className: "app-category-label",
                                    label: `Categorie ${cat}`,
                                    hexpand: true,
                                    halign: "START",
                                }),
                            ],
                        })
                        const revealer = new (Widget as any).Revealer({
                            transition: "slide_down",
                            revealChild: bind(expandedVar),
                            child: new Widget.Box({
                                vertical: true,
                                spacing: 4,
                                children: groups[cat].map(st => streamRow(st)),
                            }),
                        })
                        nodes.push(new Widget.Box({
                            vertical: true,
                            spacing: 2,
                            children: [header, revealer],
                        }))
                    })
                    return nodes
                }),
            }),
        ],
    })

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
                            className: bind(currentSinkKind).as(k => "action-button" + (k === "speaker" ? " active" : "")),
                            label: "Speakers",
                            onClicked: () => setDefaultSink("speaker"),
                        }),
                        new Widget.Button({
                            className: bind(currentSinkKind).as(k => "action-button" + (k === "headphones" ? " active" : "")),
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
