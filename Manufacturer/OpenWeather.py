from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType, DeviceAbility
from Diamon2.SmartHome3.ControlDevice.OpenWeather import OpenWeatherCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice

class OpenWeather(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.OpenWeather, room)
    
    def auth(self, api_key):
        self.api_key = api_key
        super().auth(api_key = api_key)
    def is_my_device(self, ip_address):
        return False
    def create_noip_devices(self):
        control_device = OpenWeatherCD(self.api_key)
        return [SmartDevice(control_device,self)]