from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.audio.service import Audio
from fabric.utils import truncate

from gi.repository import Playerctl

import pulsectl

from util.ui import add_hover_cursor
from config.media import HEADPHONES, AUDIO_SINKS


""" Media control and info module. """


class Media(Box):
    def __init__(self, manager, **kwargs):
        super().__init__(
            name="media",
            orientation="h",
            kwargs=kwargs
        )


        self.PLAYING_LABEL = ""
        self.PAUSED_LABEL = ""
        self.HEADPHONES_LABEL = ""
        self.SPEAKER_LABEL = "󰓃"
        self.MUTED_LABEL = ""


        self.manager = manager
        self.audio = Audio()
        self.pulse = pulsectl.Pulse()


        self.status = Label(
            name="playback-status"
        )
        self.playback_control = Button(
            child=self.status,
            on_clicked=self.toggle_play_pause,
            visible=False,
        )
        add_hover_cursor(self.playback_control)


        self.title = Label(
            name="media-title",
            visible=False
        )


        self.artist = Label(
            name="media-artist",
            visible=False
        )


        self.output_device = Label(
            name="output-device"
        )
        self.output_control = Button(
            child=self.output_device,
            on_clicked=self.swap_audio_sink
        )
        add_hover_cursor(self.output_control)


        self.children = [
            self.playback_control,
            self.title,
            self.artist,
            self.output_control,
        ]


        for name in manager.props.player_names:
            self.init_player(name)


        manager.connect("name-appeared", self.on_name_appeared)


        self.audio.connect("speaker_changed", self.on_speaker_changed)


    def toggle_play_pause(self, button):
        top_player = self.manager.props.players[0]
        if top_player:
            top_player.play_pause()
            

    def init_player(self, name):
        player = Playerctl.Player.new_from_name(name)
        player.connect("playback-status::playing", self.on_play, self.manager)
        player.connect("playback-status::paused", self.on_pause, self.manager)
        player.connect("metadata", self.on_metadata, self.manager)
        self.manager.manage_player(player)


    def on_play(self, player, status, manager):
        # show playback control button when first player apears
        self.playback_control.set_property("visible", True)
        self.status.set_property("label", self.PLAYING_LABEL)


    def on_pause(self, player, status, manager):
        self.status.set_property("label", self.PAUSED_LABEL)
        

    def on_metadata(self, player, metadata, manager):
        """ Updates title and artist of playing media. """
        if "xesam:title" in metadata.keys():
            media_title = truncate(metadata["xesam:title"], 16)
            # show title if hidden
            self.title.set_property("visible", True)
            self.title.set_property("label", media_title)
        else:
            self.title.set_property("visible", False)

        if "xesam:artist" in metadata.keys():
            media_artist = truncate(metadata["xesam:artist"][0], 16)
            # show artist if hidden
            self.artist.set_property("visible", True)
            self.artist.set_property("label", f", {media_artist}")
        else:
            self.title.set_property("visible", False)


    def on_name_appeared(self, manager, name):
        """ Automatically add new players to manager. """
        self.init_player(name)


    def on_speaker_changed(self, service):
        if service.speaker.muted:
            self.output_device.set_property("label", self.MUTED_LABEL)
        elif service.speaker.name in HEADPHONES:
            self.output_device.set_property("label", self.HEADPHONES_LABEL)
        else:
            self.output_device.set_property("label", self.SPEAKER_LABEL)

    
    def swap_audio_sink(self, *args):
        """ 
        Changes audio output by rotating through the sinks
        listed in config/media.py.
        """
        default_sink = self.pulse.sink_default_get()
        default_sink_idx = AUDIO_SINKS.index(default_sink.name)

        new_sink_idx = (default_sink_idx + 1) % len(AUDIO_SINKS)
        new_sink_name = AUDIO_SINKS[new_sink_idx]
        new_sink = self.pulse.get_sink_by_name(new_sink_name)

        self.pulse.sink_default_set(new_sink)