// ags/.config/ags/widgets/Audio.tsx

import { bind, Variable } from "astal"
import { Widget } from "astal/gtk3"
import { execAsync } from "astal/process"
import Wp from "gi://AstalWp"

const audioProfiles = [
    { name: "Stereo", command: ["pactl", "set-card-profile", "1", "HiFi (HDMI1, HDMI2, HDMI3, Headphones, Mic1, Mic2)"] },
    { name: "HDMI", command: ["pactl", "set-card-profile", "0", "output:hdmi-stereo"] }
]

export default function AudioWidget({ fullView = false }: { fullView?: boolean }) {
    const audio = Wp.get_default()
    const speaker = audio?.audio?.defaultSpeaker
    const mic = audio?.audio?.defaultMicrophone

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
                            label: "Audio Settings",
                            onClicked: () => execAsync(["pavucontrol"]).catch(console.error)
                        }),
                        new Widget.Button({
                            className: "action-button",
                            label: "EasyEffects",
                            onClicked: () => execAsync(["easyeffects"]).catch(console.error)
                        })
                    ]
                })
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
