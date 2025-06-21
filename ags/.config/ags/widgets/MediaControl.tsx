// AGS v2 Media Control Widget

import Mpris from "gi://AstalMpris"
import { bind } from "astal"

export default function MediaControlWidget({ fullView = false }: { fullView?: boolean }) {
    const mpris = Mpris.get_default()

    if (fullView) {
        return <box className="media-control-full" vertical spacing={12}>
            <label className="widget-title" label="🎵 Media Control Center" />
            
            {bind(mpris, "players").as(players => 
                players.length === 0 ? (
                    <label className="no-media" label="No media playing" />
                ) : (
                    players.map(player => (
                        <box key={player.busName} className="player-widget" vertical spacing={10}>
                            {/* Player info */}
                            <box className="player-info" spacing={12}>
                                {player.coverArt && (
                                    <box className="album-art"
                                        css={`background-image: url('${player.coverArt}')`}
                                        widthRequest={80}
                                        heightRequest={80} />
                                )}
                                <box vertical>
                                    <label className="track-title" label={bind(player, "title")} />
                                    <label className="track-artist" label={bind(player, "artist")} />
                                    <label className="track-album" label={bind(player, "album")} />
                                    <label className="player-name" label={player.identity} />
                                </box>
                            </box>

                            {/* Progress bar */}
                            <box className="progress-section" vertical spacing={4}>
                                <scale className="progress-bar"
                                    min={0}
                                    max={bind(player, "length")}
                                    value={bind(player, "position")}
                                    onDragged={({ value }) => player.position = value}
                                    drawValue={false} />
                                <box className="time-labels">
                                    <label label={bind(player, "position").as(p => {
                                        const mins = Math.floor(p / 60)
                                        const secs = Math.floor(p % 60).toString().padStart(2, '0')
                                        return `${mins}:${secs}`
                                    })} />
                                    <box hexpand />
                                    <label label={bind(player, "length").as(l => {
                                        const mins = Math.floor(l / 60)
                                        const secs = Math.floor(l % 60).toString().padStart(2, '0')
                                        return `${mins}:${secs}`
                                    })} />
                                </box>
                            </box>

                            {/* Controls */}
                            <box className="media-controls" halign={Gtk.Align.CENTER} spacing={12}>
                                <button className="control-button"
                                    onClicked={() => player.shuffle = !player.shuffle}>
                                    <icon icon="media-playlist-shuffle-symbolic" />
                                </button>
                                <button className="control-button"
                                    onClicked={() => player.previous()}>
                                    <icon icon="media-skip-backward-symbolic" />
                                </button>
                                <button className="play-pause-button"
                                    onClicked={() => player.playPause()}>
                                    <icon icon={bind(player, "playbackStatus").as(status => 
                                        status === Mpris.PlaybackStatus.PLAYING 
                                            ? "media-playback-pause-symbolic"
                                            : "media-playback-start-symbolic"
                                    )} />
                                </button>
                                <button className="control-button"
                                    onClicked={() => player.next()}>
                                    <icon icon="media-skip-forward-symbolic" />
                                </button>
                                <button className="control-button"
                                    onClicked={() => player.loop = player.loop === Mpris.Loop.NONE 
                                        ? Mpris.Loop.TRACK 
                                        : player.loop === Mpris.Loop.TRACK 
                                            ? Mpris.Loop.PLAYLIST 
                                            : Mpris.Loop.NONE}>
                                    <icon icon={bind(player, "loop").as(loop => 
                                        loop === Mpris.Loop.TRACK ? "media-playlist-repeat-song-symbolic" :
                                        loop === Mpris.Loop.PLAYLIST ? "media-playlist-repeat-symbolic" :
                                        "media-playlist-no-repeat-symbolic"
                                    )} />
                                </button>
                            </box>

                            {/* Volume */}
                            <box className="volume-section" spacing={8}>
                                <icon icon="audio-volume-medium-symbolic" />
                                <scale className="volume-slider"
                                    min={0} max={1}
                                    value={bind(player, "volume")}
                                    onDragged={({ value }) => player.volume = value}
                                    drawValue={false}
                                    hexpand={true} />
                                <label label={bind(player, "volume").as(v => `${Math.round(v * 100)}%`)} />
                            </box>
                        </box>
                    ))
                )
            )}

            {/* Quick launch media apps */}
            <box className="media-apps" spacing={6}>
                <button className="app-button" onClicked={() => execAsync(["spotify"])}>
                    Spotify
                </button>
                <button className="app-button" onClicked={() => execAsync(["cider"])}>
                    Apple Music
                </button>
                <button className="app-button" onClicked={() => execAsync(["firefox", "--new-window", "https://music.youtube.com"])}>
                    YouTube Music
                </button>
            </box>
        </box>
    }

    return <box className="media-control-compact">
        <icon icon="media-playback-start-symbolic" />
    </box>
}