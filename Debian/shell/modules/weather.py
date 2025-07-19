from typing import Literal
from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils.helpers import bulk_connect

from gi.repository import GObject

from services.weather import WeatherService

import config.icons as Icons


SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600


def lookup_weather_icon(group):
    if group in Icons.weather:
        return Icons.weather[group]
    else:
        return None


class WeatherInfo(Box):
    def __init__(self, size: Literal["large", "small"], **kwargs):
        super().__init__(
            style_classes="weather-info-small"
            if size == "small"
            else "weather-info-large",
            spacing=10,
            orientation="h" if size == "small" else "v",
            v_align="center",
            h_align="center",
            **kwargs,
        )

        self.hide()

        self.service = WeatherService.get_instance()

        bulk_connect(
            self.service,
            {
                "notify::status": self.on_status_changed,
                "notify::group": self.on_group_changed,
                "notify::temperature": self.on_temperature_changed,
            },
        )

        if size == "large":
            self.service.connect("notify::description", self.on_description_changed)
            self.description = Label(style_classes="weather-info-label", label="")

        self.weather_icon_box = Box(
            children=Label(
                style_classes="weather-icon", markup=Icons.weather["Clear-Day"]
            )
        )
        self.temperature = Label(
            style_classes="weather-info-label",
            label="",
        )
        self.temperature_icon = Label(
            style_classes="weather-icon", markup=Icons.fahrenheit
        )

        if size == "small":
            children = [self.weather_icon_box, self.temperature, self.temperature_icon]
        else:
            # initialize description label
            self.on_description_changed(self.service, GObject.ParamSpecString())
            children = [
                Box(
                    spacing=10,
                    orientation="h",
                    h_align="center",
                    children=[
                        self.weather_icon_box,
                        self.temperature,
                        self.temperature_icon,
                    ],
                ),
                self.description,
            ]

        self.children = children

    def on_status_changed(self, service, _):
        if service.status:
            self.show_all()
        else:
            self.hide()

    def on_group_changed(self, service, _):
        icon = lookup_weather_icon(service.group)

        if icon is not None:
            self.weather_icon_box.children = Label(
                style_classes="weather-icon", markup=icon
            )

    def on_temperature_changed(self, service, _):
        self.temperature.set_property("label", str(service.temperature))

    def on_description_changed(self, service, _):
        self.description.set_property("label", service.description)
