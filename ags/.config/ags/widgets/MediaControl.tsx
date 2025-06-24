// ags/.config/ags/widgets/MediaControl.tsx

import Mpris from "gi://AstalMpris"
import { execAsync } from "astal/process"
import { bind } from "astal"
import { Widget } from "astal/gtk3"
import Gtk from "gi://Gtk?version=3.0"

export default function MediaControlWidget({ fullView = false }: { fullView?: boolean }) {
    const mpris = Mpris.get_default()

    if (fullView) {
        return new Widget.Box({
            className: "media-control-full",
            vertical: true,
            spacing: 12,
            children: [
                new Widget.Label({
                    className: "widget-title",
                    label: "🎵 Media Control Center"
                }),
                
                bind(mpris, "players").as(players => 
                    players.length === 0 ? new Widget.Label({
                        className: "no-media",
                        label: "No media playing"
                    }) : new Widget.Box({
                        vertical: true,
                        spacing: 12,
                        children: players.map(player => new Widget.Box({
                            className: "player-widget",
                            vertical: true,
                            spacing: 10,
                            children: [
                                // Player info
                                new Widget.Box({
                                    className: "player-info",
                                    spacing: 12,
                                    children: [
                                        player.coverArt ? new Widget.Box({
                                            className: "album-art"
                                        }) : new Widget.Box({}),
                                        new Widget.Box({
                                            vertical: true,
                                            children: [
                                                new Widget.Label({
                                                    className: "track-title",
                                                    label: bind(player, "title")
                                                }),
                                                new Widget.Label({
                                                    className: "track-artist",
                                                    label: bind(player, "artist")
                                                }),
                                                new Widget.Label({
                                                    className: "track-album",
                                                    label: bind(player, "album")
                                                }),
                                                new Widget.Label({
                                                    className: "player-name",
                                                    label: player.identity
                                                })
                                            ]
                                        })
                                    ]
                                }),

                                // Progress bar
                                new Widget.Box({
                                    className: "progress-section",
                                    vertical: true,
                                    spacing: 4,
                                    children: [
                                        // @ts-ignore - Scale widget
                                        new Widget.Scale({
                                            className: "progress-bar",
                                            min: 0,
                                            max: bind(player, "length"),
                                            value: bind(player, "position"),
                                            onDragged: ({ value }: any) => player.position = value,
                                            drawValue: false
                                        }),
                                        new Widget.Box({
                                            className: "time-labels",
                                            children: [
                                                new Widget.Label({
                                                    label: bind(player, "position").as(p => {
                                                        const mins = Math.floor(p / 60)
                                                        const secs = Math.floor(p % 60).toString().padStart(2, '0')
                                                        return `${mins}:${secs}`
                                                    })
                                                }),
                                                new Widget.Box({ hexpand: true }),
                                                new Widget.Label({
                                                    label: bind(player, "length").as(l => {
                                                        const mins = Math.floor(l / 60)
                                                        const secs = Math.floor(l % 60).toString().padStart(2, '0')
                                                        return `${mins}:${secs}`
                                                    })
                                                })
                                            ]
                                        })
                                    ]
                                }),

                                // Controls
                                new Widget.Box({
                                    className: "media-controls",
                                    halign: Gtk.Align.CENTER,
                                    spacing: 12,
                                    children: [
                                        new Widget.Button({
                                            className: "control-button",
                                            onClicked: () => player.shuffle = !player.shuffle,
                                            child: new Widget.Icon({ icon: "media-playlist-shuffle-symbolic" })
                                        }),
                                        new Widget.Button({
                                            className: "control-button",
                                            onClicked: () => player.previous(),
                                            child: new Widget.Icon({ icon: "media-skip-backward-symbolic" })
                                        }),
                                        new Widget.Button({
                                            className: "play-pause-button",
                                            onClicked: () => player.playPause(),
                                            child: new Widget.Icon({
                                                icon: bind(player, "playbackStatus").as(status => 
                                                    status === Mpris.PlaybackStatus.PLAYING 
                                                        ? "media-playback-pause-symbolic"
                                                        : "media-playback-start-symbolic"
                                                )
                                            })
                                        }),
                                        new Widget.Button({
                                            className: "control-button",
                                            onClicked: () => player.next(),
                                            child: new Widget.Icon({ icon: "media-skip-forward-symbolic" })
                                        }),
                                        new Widget.Button({
                                            className: "control-button",
                                            onClicked: () => player.loop = player.loop === Mpris.Loop.NONE 
                                                ? Mpris.Loop.TRACK 
                                                : player.loop === Mpris.Loop.TRACK 
                                                    ? Mpris.Loop.PLAYLIST 
                                                    : Mpris.Loop.NONE,
                                            child: new Widget.Icon({
                                                icon: bind(player, "loop").as(loop => 
                                                    loop === Mpris.Loop.TRACK ? "media-playlist-repeat-song-symbolic" :
                                                    loop === Mpris.Loop.PLAYLIST ? "media-playlist-repeat-symbolic" :
                                                    "media-playlist-no-repeat-symbolic"
                                                )
                                            })
                                        })
                                    ]
                                }),

                                // Volume
                                new Widget.Box({
                                    className: "volume-section",
                                    spacing: 8,
                                    children: [
                                        new Widget.Icon({ icon: "audio-volume-medium-symbolic" }),
                                        // @ts-ignore - Scale widget
                                        new Widget.Scale({
                                            className: "volume-slider",
                                            min: 0,
                                            max: 1,
                                            value: bind(player, "volume"),
                                            onDragged: ({ value }: any) => player.volume = value,
                                            drawValue: false,
                                            hexpand: true
                                        }),
                                        new Widget.Label({
                                            label: bind(player, "volume").as(v => `${Math.round(v * 100)}%`)
                                        })
                                    ]
                                })
                            ]
                        }))
                    })
                ),

                // Quick launch media apps
                new Widget.Box({
                    className: "media-apps",
                    spacing: 6,
                    children: [
                        new Widget.Button({
                            className: "app-button",
                            label: "Spotify",
                            onClicked: () => execAsync(["spotify"])
                        }),
                        new Widget.Button({
                            className: "app-button",
                            label: "Apple Music",
                            onClicked: () => execAsync(["cider"])
                        }),
                        new Widget.Button({
                            className: "app-button",
                            label: "YouTube Music",
                            onClicked: () => execAsync(["firefox", "--new-window", "https://music.youtube.com"])
                        })
                    ]
                })
            ]
        })
    }

    return new Widget.Box({
        className: "media-control-compact",
        children: [new Widget.Icon({ icon: "media-playback-start-symbolic" })]
    })
}
