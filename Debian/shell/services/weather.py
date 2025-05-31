from fabric import Service, Property, Signal

from gi.repository import GLib
import asyncio
import aiohttp

from config.weather import WEATHER_API_URL


class WeatherService(Service):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._status = True
        self._group = "",
        self._description = ""
        self._temperature = 0.0

        self.start()


    @Property(str, flags="read-write")
    def group(self) -> str:
        return self._group
    

    @group.setter
    def group(self, new_group):
        self._group = new_group
        self.group_changed(new_group)


    @Signal
    def group_changed(self, new_group: str) -> None:...


    @Property(float, flags="read-write")
    def temperature(self) -> float:
        return self._temperature
    

    @temperature.setter
    def temperature(self, new_temperature: float):
        self._temperature = new_temperature
        self.temperature_changed(new_temperature)


    @Signal
    def temperature_changed(self, new_temperature: float) -> None:...


    @Property(bool, default_value=True, flags="read-write")
    def status(self) -> bool:
        return self._status
    

    @status.setter
    def status(self, new_status: bool):
        self._staus = new_status
        self.status_changed(new_status)


    @Signal
    def status_changed(self, new_status: bool) -> None:...


    async def retrieve_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL) as response:

                if response.status != 200:
                    self.status = False
                    return True
                
                self.status = True
                
                response = await response.json()
                
                weather_group = response["weather"][0]["main"]
                current_temperature = response["main"]["temp"]

                self.group = weather_group
                self.temperature = current_temperature

                return True
            

    def start(self):
        asyncio.run(self.retrieve_data())

        GLib.timeout_add_seconds(
            120, # 2 secs 
            lambda *_: asyncio.run(self.retrieve_data())
        )