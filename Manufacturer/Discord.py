from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType
from Diamon2.SmartHome3.ControlDevice.Discord import DiscordCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice



class Discord(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.Discord, room)
    
    def auth(self, api_key):
        self.api_key = api_key
        super().auth(api_key = api_key)

    def is_my_device(self, ip_address):
        return False
    
    def create_noip_devices(self):
        return [SmartDevice(DiscordCD(self.api_key),self)]