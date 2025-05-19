from fabric.widgets.box import Box
from fabric.widgets.eventbox import EventBox
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.audio.service import Audio
from fabric.widgets.wayland import WaylandWindow as Window
from fabric.widgets.image import Image
from fabric.utils import truncate, bulk_connect

from gi.repository import Playerctl, GdkPixbuf

import pulsectl

from util.ui import add_hover_cursor, toggle_visible
from util.helpers import get_file_path_from_mpris_url
from config.media import HEADPHONES
from config.icons import ICONS, SMALL_ICON_SIZE


""" Side Media control and info module. """


class Media(Window):
    def __init__(self, manager, **kwargs):
        super().__init__(
            name="media",
            anchor="top left",
            exclusivity="normal",
            layer="top",
            margin="10px 0px 0px 20px",
            kwargs=kwargs
        )

        self.manager = manager
        self.audio = Audio()
        self.pulse = pulsectl.Pulse()
        self.media_panel = MediaPanel()


        """ self.output_device_label = Label(
            style_classes=["text-icon", "media-controls"]
        ) """
        self.output_icon = Image(
            icon_name=ICONS["speaker"],
            icon_size=SMALL_ICON_SIZE,
            style_classes="media-control-icon"
        )
        self.output_control = Button(
            child=self.output_icon,
            on_clicked=self.swap_audio_sink
        )
        add_hover_cursor(self.output_control)

        
        self.skip_prev_icon = Image(
            icon_name=ICONS["skip-prev"],
            icon_size=SMALL_ICON_SIZE,
            style_classes="media-control-icon"
        )
        self.prev_track_control = Button(
            child=self.skip_prev_icon,
            on_clicked=self.skip_to_prev_track
        )
        add_hover_cursor(self.prev_track_control)


        self.play_icon = Image(
            icon_name=ICONS["play"],
            icon_size=SMALL_ICON_SIZE,
            style_classes="media-control-icon"
        )
        self.play_control = Button(
            child=self.play_icon,
            on_clicked=self.toggle_play_pause,
        )
        add_hover_cursor(self.play_control)


        self.skip_next_icon = Image(
            icon_name=ICONS["skip-next"],
            icon_size=SMALL_ICON_SIZE,
            style_classes="media-control-icon"
        )
        self.next_track_control = Button(
            child=self.skip_next_icon,
            on_clicked=self.skip_to_next_track
        )
        add_hover_cursor(self.next_track_control)


        self.title = Label(
            style_classes="info-box-text",
        )
        self.artist = Label(
            style_classes="info-box-text",
        )
        self.info_box = Box(
            name="info-box",
            children=[
                self.title,
                self.artist
            ]
        )
        self.media_info = EventBox(
            name="media-info",
            orientation="h",
            child=self.info_box,
            visible=False,
            events=["enter-notify", "leave-notify"]
        )


        bulk_connect(
            self.media_info, 
            {
                "enter-notify-event": self.show_media_info_panel,
                "leave-notify-event": self.hide_media_info_panel
            }
        )


        self.children = Box(
            spacing=10,
            orientation="h",
            children=[
                self.media_info,
                self.output_control,
                self.prev_track_control,
                self.play_control,
                self.next_track_control
            ]
        ) 


        for name in manager.props.player_names:
            self.init_player(name)


        manager.connect("name-appeared", self.on_name_appeared)


        self.audio.connect("speaker_changed", self.on_speaker_changed)


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
        # show playback control button when first player apears
        self.play_icon.set_property("icon_name", ICONS["play"])


    def on_pause(self, player, status, manager):
        self.play_icon.set_property("icon_name", ICONS["pause"])


    def on_metadata(self, player, metadata, manager):
        """
        Update media info on bar and on media panel
        """
        if "xesam:title" in metadata.keys() and metadata['xesam:title'] != "":
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

        if "xesam:artist" in metadata.keys() and metadata['xesam:artist'] != [""]:
            self.media_info.set_property("visible", True)

            artist_str = metadata["xesam:artist"][0]
            # add space and comma between title and artist when title is visible
            if self.title.get_property("visible"):
                self.artist.set_property("label", f", {artist_str}")
            else:
                self.artist.set_property("label", artist_str)
            self.artist.set_property("visible", True)

            self.media_panel.artist.set_property("label", artist_str)
            self.media_panel.artist.set_property("visible", True)

            self.media_info.set_property("visible", True)
        else:
            self.artist.set_property("visible", False)
            self.media_panel.artist.set_property("visible", False)

        if "xesam:title" in metadata.keys() and metadata['xesam:title'] == "" and \
                "xesam:artist" in metadata.keys() and metadata['xesam:artist'] == [""]:
            self.media_info.set_property("visible", False)

        if "xesam:album" in metadata.keys() and metadata["xesam:album"] != "":
            self.media_panel.album.set_property("label", metadata["xesam:album"])
            self.media_panel.album.set_property("visible", True)
        else:
            self.media_panel.album.set_property("visible", False)
        
        if "mpris:artUrl" in metadata.keys():
            file_path = get_file_path_from_mpris_url(metadata["mpris:artUrl"])
            art_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(file_path, 300, 300, True)
            self.media_panel.art.set_property("pixbuf", art_pixbuf)
            self.media_panel.art.set_property("visible", True)
        else:
            self.media_panel.art.set_property("visible", False) 


    def on_name_appeared(self, manager, name):
        """ Automatically add new players to manager. """
        self.init_player(name)


    def on_speaker_changed(self, service):
        if service.speaker.name in HEADPHONES:
            new_icon_name = ICONS["headphones"]
        else:
            new_icon_name = ICONS["speaker"]

        self.output_icon.set_property("icon_name", new_icon_name)

    
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
        except:
            pass
            


    def show_media_info_panel(self, *args):
        toggle_visible(self.media_panel)


    def hide_media_info_panel(self, *args):
        toggle_visible(self.media_panel)


class MediaPanel(Window):
    def __init__(self, **kwargs):
        super().__init__(
            name="media-info-panel",
            layer="top",
            anchor="left top",
            exclusivity="none",
            margin="20px 0px 0px 20px",
            visible=False
        )


        self.art = Image(
            name="media-art",
            visible=False
        )


        self.title = Label(
            style_classes="media-info-panel-text",
            visible=False,
            line_wrap="word"
        )
        

        self.artist = Label(
            style_classes="media-info-panel-text",
            visible=False,
            line_wrap="word"
        )


        self.album = Label(
            style_classes="media-info-panel-text",
            visible=False,
            line_wrap="word"
        )


        self.box = Box(
            name="media-info-panel-box",
            orientation='v',
            v_align="center",
            spacing=10,
            children=[
                self.art,
                self.title,
                self.artist,
                self.album
            ]
        )


        self.children = self.box