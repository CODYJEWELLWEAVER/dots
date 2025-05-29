from fabric import Service, Property, Signal

from openweathermap import API_KEY

from gi.repository import GLib


class WeatherService(Service):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        GLib.timeout_add_seconds(
            1,
            lambda: print("Hello")
        )



    @Property(str, flags="read-write")
    def description(self) -> str:
        return self._description
    

    @description.setter
    def description(self, new_description: str):
        self._description = new_description
        self.description_changed(new_description)


    @Signal
    def description_changed(self, new_description: str) -> None:...


    @Property(float, flags="read-write")
    def temperature(self) -> float:
        return self._temperature
    

    @temperature.setter
    def temperature(self, new_temperature: float):
        self._temperature = new_temperature
        self.temperature_changed(new_temperature)


    @Signal
    def temperature_changed(self, new_temperature: float) -> None:...