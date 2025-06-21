import { bind } from "astal"
import { Widget } from "astal/gtk3"
import { execAsync } from "astal/process"
import Wp from "gi://AstalWp"

export default function AudioWidget({ fullView = false }: { fullView?: boolean }) {
    try {
        const audio = Wp.get_default()
        const speaker = audio?.audio?.defaultSpeaker
        const mic = audio?.audio?.defaultMicrophone

        if (!audio) {
            return Widget.Box({
                className: "audio-widget-error",
                vertical: true,
                children: [
                    Widget.Label({ label: "Audio service not available" })
                ]
            })
        }

        if (fullView) {
            return Widget.Box({
                className: "audio-widget-full",
                vertical: true,
                spacing: 12,
                children: [
                    Widget.Label({
                        className: "widget-title",
                        label: "🎵 Audio Control"
                    }),
                    
                    // Speaker section
                    speaker ? Widget.Box({
                        className: "speaker-section",
                        vertical: true,
                        spacing: 8,
                        children: [
                            Widget.Label({
                                className: "section-label",
                                label: "Speaker"
                            }),
                            Widget.Box({
                                spacing: 12,
                                children: [
                                    Widget.Button({
                                        className: "mute-button",
                                        onClicked: () => speaker?.set_mute(!speaker.mute),
                                        child: Widget.Icon({
                                            icon: bind(speaker, "volumeIcon").as(i => i || "audio-volume-medium-symbolic")
                                        })
                                    }),
                                    Widget.Scale({
                                        className: "volume-slider",
                                        drawValue: false,
                                        hexpand: true,
                                        min: 0,
                                        max: 1,
                                        value: bind(speaker, "volume").as(v => v || 0),
                                        onDragged: ({ value }) => {
                                            if (speaker) speaker.volume = value
                                        }
                                    }),
                                    Widget.Label({
                                        className: "volume-label",
                                        label: bind(speaker, "volume").as(v => `${Math.round((v || 0) * 100)}%`)
                                    })
                                ]
                            })
                        ]
                    }) : Widget.Box(),

                    // Microphone section
                    mic ? Widget.Box({
                        className: "mic-section",
                        vertical: true,
                        spacing: 8,
                        children: [
                            Widget.Label({
                                className: "section-label",
                                label: "Microphone"
                            }),
                            Widget.Box({
                                spacing: 12,
                                children: [
                                    Widget.Button({
                                        className: "mute-button",
                                        onClicked: () => mic?.set_mute(!mic.mute),
                                        child: Widget.Icon({
                                            icon: bind(mic, "volumeIcon").as(i => i || "microphone-sensitivity-medium-symbolic")
                                        })
                                    }),
                                    Widget.Scale({
                                        className: "volume-slider",
                                        drawValue: false,
                                        hexpand: true,
                                        min: 0,
                                        max: 1,
                                        value: bind(mic, "volume").as(v => v || 0),
                                        onDragged: ({ value }) => {
                                            if (mic) mic.volume = value
                                        }
                                    }),
                                    Widget.Label({
                                        className: "volume-label",
                                        label: bind(mic, "volume").as(v => `${Math.round((v || 0) * 100)}%`)
                                    })
                                ]
                            })
                        ]
                    }) : Widget.Box(),

                    // Audio profiles
                    Widget.Box({
                        className: "audio-profiles",
                        vertical: true,
                        spacing: 8,
                        children: [
                            Widget.Label({
                                className: "section-label",
                                label: "Audio Profiles"
                            }),
                            Widget.Box({
                                spacing: 6,
                                children: [
                                    Widget.Button({
                                        className: "profile-button",
                                        label: "Stereo",
                                        onClicked: () => execAsync(["pactl", "set-card-profile", "0", "output:analog-stereo"]).catch(console.error)
                                    }),
                                    Widget.Button({
                                        className: "profile-button",
                                        label: "HDMI",
                                        onClicked: () => execAsync(["pactl", "set-card-profile", "0", "output:hdmi-stereo"]).catch(console.error)
                                    })
                                ]
                            })
                        ]
                    }),

                    // Quick actions
                    Widget.Box({
                        className: "audio-actions",
                        spacing: 6,
                        children: [
                            Widget.Button({
                                className: "action-button",
                                label: "Audio Settings",
                                onClicked: () => execAsync(["pavucontrol"]).catch(console.error)
                            }),
                            Widget.Button({
                                className: "action-button",
                                label: "EasyEffects",
                                onClicked: () => execAsync(["easyeffects"]).catch(console.error)
                            })
                        ]
                    })
                ]
            })
        }

        // Compact view
        return Widget.Box({
            className: "audio-widget-compact",
            children: [
                Widget.Icon({
                    icon: speaker ? bind(speaker, "volumeIcon").as(i => i || "audio-volume-medium-symbolic") : "audio-volume-medium-symbolic"
                })
            ]
        })
    } catch (error) {
        console.error("Audio widget error:", error)
        return Widget.Box({
            className: "audio-widget-error",
            children: [Widget.Label({ label: "Audio Error" })]
        })
    }
}