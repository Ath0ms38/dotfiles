// AGS v2 Audio Widget

import { bind, Variable } from "astal"
import Wp from "gi://AstalWp"
import { execAsync } from "astal/process"

export default function AudioWidget({ fullView = false }: { fullView?: boolean }) {
    const audio = Wp.get_default()
    const speaker = audio?.audio.defaultSpeaker
    const mic = audio?.audio.defaultMicrophone

    if (fullView) {
        return <box className="audio-widget-full" vertical spacing={12}>
            <label className="widget-title" label="🎵 Audio Control" />
            
            {/* Speaker section */}
            <box className="speaker-section" vertical spacing={8}>
                <label className="section-label" label="Speaker" />
                <box spacing={12}>
                    <button className="mute-button"
                        onClicked={() => speaker?.set_mute(!speaker.mute)}>
                        <icon icon={bind(speaker, "volumeIcon")} />
                    </button>
                    <scale className="volume-slider"
                        min={0} max={1}
                        value={bind(speaker, "volume")}
                        onDragged={({ value }) => speaker && (speaker.volume = value)}
                        drawValue={false}
                        hexpand={true} />
                    <label className="volume-label"
                        label={bind(speaker, "volume").as(v => `${Math.round(v * 100)}%`)} />
                </box>
            </box>

            {/* Microphone section */}
            <box className="mic-section" vertical spacing={8}>
                <label className="section-label" label="Microphone" />
                <box spacing={12}>
                    <button className="mute-button"
                        onClicked={() => mic?.set_mute(!mic.mute)}>
                        <icon icon={bind(mic, "volumeIcon")} />
                    </button>
                    <scale className="volume-slider"
                        min={0} max={1}
                        value={bind(mic, "volume")}
                        onDragged={({ value }) => mic && (mic.volume = value)}
                        drawValue={false}
                        hexpand={true} />
                    <label className="volume-label"
                        label={bind(mic, "volume").as(v => `${Math.round(v * 100)}%`)} />
                </box>
            </box>

            {/* Audio profiles */}
            <box className="audio-profiles" vertical spacing={8}>
                <label className="section-label" label="Audio Profiles" />
                <box spacing={6}>
                    <button className="profile-button" onClicked={() => execAsync(["pactl", "set-card-profile", "0", "output:analog-stereo"])}>
                        Stereo
                    </button>
                    <button className="profile-button" onClicked={() => execAsync(["pactl", "set-card-profile", "0", "output:hdmi-stereo"])}>
                        HDMI
                    </button>
                </box>
            </box>

            {/* Quick actions */}
            <box className="audio-actions" spacing={6}>
                <button className="action-button" onClicked={() => execAsync(["pavucontrol"])}>
                    Audio Settings
                </button>
                <button className="action-button" onClicked={() => execAsync(["easyeffects"])}>
                    EasyEffects
                </button>
            </box>
        </box>
    }

    // Compact view for waybar
    return <box className="audio-widget-compact">
        <icon icon={bind(speaker, "volumeIcon")} />
    </box>
}