from fabric.widgets.box import Box
from fabric.widgets.label import Label
from fabric.utils.helpers import bulk_connect

from services.weather import WeatherService

import config.icons as icons

import time


SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600


class WeatherInfo(Box):
    def __init__(self, bar=True, **kwargs):
        super().__init__(
            name="weather-info" if bar else "",
            spacing=10,
            v_align="center",
            h_align="center",
            **kwargs
        )


        self.hide()


        self.service = WeatherService.get_instance()


        bulk_connect(
            self.service,
            {
                "notify::status": self.on_status_changed,
                "notify::group": self.on_group_changed,
                "notify::temperature": self.on_temperature_changed
            }
        )


        self.weather_icon = Label(
            style_classes="weather-icon",
            markup=icons.weather["Clear-Day"]
        )
        self.temperature = Label(
            name="weather-temp",
            label="",
        )
        self.temperature_icon = Label(
            style_classes="weather-icon",
            markup=icons.fahrenheit
        )


        # run callbacks to initialize
        self.on_status_changed(self.service, None)
        self.on_group_changed(self.service, None)
        self.on_temperature_changed(self.service, None)


        self.children = [
            self.weather_icon,
            self.temperature,
            self.temperature_icon
        ]



    def on_status_changed(self, service, _):
        if service.status:
            self.show_all()
        else:
            self.hide()


    def on_group_changed(self, service, _):
        icon = self.lookup_weather_icon(service.group)

        if icon != None:
            self.weather_icon = Label(
                style_classes="weather-icon",
                markup=icon
            )


    def on_temperature_changed(self, service, _):
        self.temperature.set_property("label", str(service.temperature))

    
    def lookup_weather_icon(self, group):
        if group == "Clear":
            epoch_time = time.time()
            if time.daylight != 0:
                tz_offset = time.altzone
            else:
                tz_offset = time.timezone

            day_time = (epoch_time - tz_offset) % SECONDS_PER_DAY

            #             5AM                  8PM
            if day_time < 18000 or day_time >= 72000:
                group = "Clear-Night"
            else:
                group = "Clear-Day"

        if group in icons.weather:
            return icons.weather[group]
        else:
            return None