from fabric.widgets.box import Box
from fabric.widgets.eventbox import EventBox
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.audio.service import Audio
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.scale import Scale
from fabric.utils import truncate, bulk_connect

from gi.repository import Playerctl, GdkPixbuf

import pulsectl
from loguru import logger

from services.volume import VolumeService
from widgets.custom_image import CustomImage
from util.ui import add_hover_cursor, toggle_visible
from util.helpers import get_file_path_from_mpris_url
from config.media import HEADPHONES
import config.icons as Icons


""" Side Media control and info module. """


# I need to update this quite a bit. Was one of the first modules I wrote
# and I have learned a lot... I could do this much better.


class MediaControl(Box):
    def __init__(self, player_manager, **kwargs):
        super().__init__(
            name="media-control",
            spacing=10,
            v_align="center",
            h_align="center",
            **kwargs,
        )

        self.manager = player_manager
        self.audio = Audio()
        self.pulse = pulsectl.Pulse()
        self.volume_service = VolumeService.get_instance()
        self.media_panel = MediaPanel()

        self.title = Label(
            name="info-box-title",
        )
        self.artist = Label(
            name="info-box-artist",
        )
        self.info_box = Box(
            name="info-box",
            orientation="v",
            v_align="center",
            h_align="center",
            children=[self.title, self.artist],
        )
        self.media_info = EventBox(
            child=self.info_box, visible=False, events=["enter-notify", "leave-notify"]
        )

        bulk_connect(
            self.media_info,
            {
                "enter-notify-event": self.show_media_info_panel,
                "leave-notify-event": self.hide_media_info_panel,
            },
        )

        self.output_control = Button(
            child=Label(style_classes="media-control-icon", markup=Icons.speaker),
            on_clicked=self.swap_audio_sink,
        )
        add_hover_cursor(self.output_control)

        self.prev_track_control = Button(
            child=Label(style_classes="media-control-icon", markup=Icons.skip_prev),
            on_clicked=self.skip_to_prev_track,
        )
        add_hover_cursor(self.prev_track_control)

        self.play_control_label = Label(
            style_classes="media-control-icon", markup=Icons.play
        )
        self.play_control = Button(
            child=self.play_control_label,
            on_clicked=self.toggle_play_pause,
        )
        add_hover_cursor(self.play_control)

        self.next_track_control = Button(
            child=Label(style_classes="media-control-icon", markup=Icons.skip_next),
            on_clicked=self.skip_to_next_track,
        )
        add_hover_cursor(self.next_track_control)

        self.volume_scale = Scale(
            name="volume-scale",
            increments=(0.01, 0.1),
            h_align="center",
            value=self.volume_service.volume,
        )
        self.volume_scale.connect("change-value", self.on_volume_slider_value_change)
        add_hover_cursor(self.volume_scale)

        self.children = [
            self.media_info,
            self.output_control,
            self.prev_track_control,
            self.play_control,
            self.next_track_control,
            self.volume_scale,
        ]

        for name in player_manager.props.player_names:
            self.init_player(name)

        player_manager.connect("name-appeared", self.on_name_appeared)

        self.audio.connect("speaker_changed", self.on_speaker_changed)

        self.volume_service.connect("changed", self.set_volume_scale_value)

    def set_volume_scale_value(self, *args):
        volume = self.volume_service.volume if not self.volume_service.is_muted else 0
        self.volume_scale.value = volume

    def toggle_play_pause(self, *args):
        players = self.manager.props.players
        if players:
            players[0].play_pause()

    def skip_to_prev_track(self, *args):
        players = self.manager.props.players
        if players:
            players[0].previous()

    def skip_to_next_track(self, *args):
        players = self.manager.props.players
        if players:
            players[0].next()

    def init_player(self, name):
        player = Playerctl.Player.new_from_name(name)
        player.connect("playback-status::playing", self.on_play, self.manager)
        player.connect("playback-status::paused", self.on_pause, self.manager)
        player.connect("playback-status::stopped", self.on_pause, self.manager)
        player.connect("metadata", self.on_metadata, self.manager)
        self.manager.manage_player(player)

    def on_play(self, player, status, manager):
        label = Label(style_classes="media-control-icon", markup=Icons.pause)

        self.play_control.children = label

    def on_pause(self, player, status, manager):
        label = Label(style_classes="media-control-icon", markup=Icons.play)

        self.play_control.children = label

    def on_metadata(self, player, metadata, manager):
        """
        Update media info on bar and on media panel
        """
        self.update_title(metadata)

        self.update_artist(metadata)

        self.update_media_info_visibility(metadata)

        self.update_album(metadata)

        self.update_art(metadata)

    def update_title(self, metadata: dict):
        if "xesam:title" in metadata.keys() and metadata["xesam:title"] != "":
            self.media_info.set_property("visible", True)

            title_str = metadata["xesam:title"]
            self.title.set_property("label", truncate(title_str, 24))
            self.title.set_property("visible", True)

            self.media_panel.title.set_property("label", title_str)
            self.media_panel.title.set_property("visible", True)

            self.media_info.set_property("visible", True)
        else:
            self.title.set_property("visible", False)
            self.media_panel.title.set_property("visible", False)

    def update_artist(self, metadata: dict):
        if "xesam:artist" in metadata.keys() and metadata["xesam:artist"] != [""]:
            self.media_info.set_property("visible", True)

            artist_str = metadata["xesam:artist"][0]
            # add space and comma between title and artist when title is visible
            if self.title.get_property("visible"):
                self.artist.set_property("label", truncate(artist_str, 24))
            else:
                self.artist.set_property("label", artist_str)
            self.artist.set_property("visible", True)

            self.media_panel.artist.set_property("label", artist_str)
            self.media_panel.artist.set_property("visible", True)

            self.media_info.set_property("visible", True)
        else:
            self.artist.set_property("visible", False)
            self.media_panel.artist.set_property("visible", False)

    def update_media_info_visibility(self, metadata: dict):
        if (
            "xesam:title" in metadata.keys()
            and metadata["xesam:title"] == ""
            and "xesam:artist" in metadata.keys()
            and metadata["xesam:artist"] == [""]
        ):
            self.media_info.set_property("visible", False)

    def update_album(self, metadata: dict):
        if "xesam:album" in metadata.keys() and metadata["xesam:album"] != "":
            self.media_panel.album.set_property("label", metadata["xesam:album"])
            self.media_panel.album.set_property("visible", True)
        else:
            self.media_panel.album.set_property("visible", False)

    def update_art(self, metadata: dict):
        if "mpris:artUrl" in metadata.keys():
            file_path = get_file_path_from_mpris_url(metadata["mpris:artUrl"])
            self_width = self.get_preferred_width().natural_width
            art_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                file_path, self_width - 60, self_width - 60, True
            )
            self.media_panel.art.set_property("pixbuf", art_pixbuf)
            self.media_panel.art.set_property("visible", True)
        else:
            self.media_panel.art.set_property("visible", False)

    def on_name_appeared(self, manager, name):
        """Automatically add new players to manager."""
        self.init_player(name)

    def on_speaker_changed(self, service):
        if service.speaker.name in HEADPHONES:
            icon = Icons.headphones
        else:
            icon = Icons.speaker

        label = Label(style_classes="media-control-icon", markup=icon)

        self.output_control.children = label

    def swap_audio_sink(self, button):
        """
        Changes audio output by rotating through the sinks
        detected by pulse audio.
        """
        sink_names = [sink.name for sink in self.pulse.sink_list()]
        default_sink = self.pulse.sink_default_get()
        default_sink_idx = sink_names.index(default_sink.name)

        new_sink_idx = (default_sink_idx + 1) % len(sink_names)
        new_sink_name = sink_names[new_sink_idx]

        try:
            new_sink = self.pulse.get_sink_by_name(new_sink_name)
            self.pulse.sink_default_set(new_sink)
        except pulsectl.pulsectl.PulseIndexError:
            logger.error(f"Could not set default sink: {new_sink_name}")

    def on_volume_slider_value_change(self, widget, event, value):
        if value < 0:
            value = 0
        elif value > 1:
            value = 1

        sink = self.pulse.sink_default_get()

        # unmute sink on slide
        if sink.mute and value > 0:
            self.pulse.sink_mute(sink.index, False)

        sink_volume = sink.volume
        sink_volume.value_flat = value
        self.pulse.sink_volume_set(sink.index, sink_volume)

    def get_pulse_volume(self, *args):
        sink = self.pulse.sink_default_get()
        return 0 if sink.mute else sink.volume.value_flat

    def show_media_info_panel(self, *args):
        toggle_visible(self.media_panel)

    def hide_media_info_panel(self, *args):
        toggle_visible(self.media_panel)


class MediaPanel(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="media-info-panel",
            layer="overlay",
            anchor="left top",
            exclusivity="none",
            visible=False,
            margin="20px 0px 0px 322px",
            **kwargs,
        )

        self.art = CustomImage(name="media-art", visible=False)

        self.title = Label(
            style_classes="media-info-panel-text", visible=False, line_wrap="word"
        )

        self.artist = Label(
            style_classes="media-info-panel-text", visible=False, line_wrap="word"
        )

        self.album = Label(
            style_classes="media-info-panel-text", visible=False, line_wrap="word"
        )

        self.box = Box(
            name="media-info-panel-box",
            orientation="v",
            v_align="center",
            spacing=10,
            children=[
                Box(
                    name="media-art-box",
                    children=self.art,
                    v_expand=True,
                    h_expand=True,
                ),
                self.title,
                self.artist,
                self.album,
            ],
        )

        self.children = self.box
