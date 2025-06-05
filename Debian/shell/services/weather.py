from fabric import Service, Property

from util.singleton import Singleton

from gi.repository import GLib
import asyncio
import aiohttp
from loguru import logger
import time

from config.weather import WEATHER_API_URL


class WeatherService(Service, Singleton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._loop = asyncio.get_event_loop()

        self._status = True
        self._group = ""
        self._description = ""
        self._temperature = 0.0

        self.start()

    @Property(str, flags="read-write")
    def group(self) -> str:
        return self._group

    @group.setter
    def group(self, new_group: str):
        self._group = new_group

    @Property(str, flags="read-write")
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, new_description: str):
        self._description = new_description

    @Property(int, flags="read-write")
    def temperature(self) -> int:
        return self._temperature

    @temperature.setter
    def temperature(self, new_temperature: int):
        self._temperature = new_temperature

    @Property(bool, default_value=True, flags="read-write")
    def status(self) -> bool:
        return self._status

    @status.setter
    def status(self, new_status: bool):
        self._staus = new_status

    async def retrieve_data(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL) as response:
                logger.debug("Fetching weather data...")

                if response.status != 200:
                    self.status = False
                    return True

                self.status = True

                response = await response.json()

                weather = response["weather"][0]
                weather_group = weather["main"]
                current_temperature = response["main"]["temp"]
                weather_description = weather["description"]

                sunrise = response["sys"]["sunrise"]
                sunset = response["sys"]["sunset"]
                cur_time = time.time()
                if sunrise <= cur_time <= sunset and weather_group == "Clear":
                    weather_group = "Clear-Day"
                else:
                    weather_group = "Clear-Night"

                logger.debug(f"Weather group: {weather_group}")

                self.group = weather_group
                self.description = weather_description
                self.temperature = current_temperature

                return True

    def start(self):
        self._loop.create_task(self.retrieve_data())

        GLib.timeout_add_seconds(
            120,  # 2 min
            lambda *_: self._loop.create_task(self.retrieve_data()),
        )
