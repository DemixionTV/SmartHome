from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType, DeviceAbility
from Diamon2.SmartHome3.ControlDevice.OpenRGB import OpenRGBCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from Diamon2.Progr.Net import getOS, getSubnet, checkPort
from Diamon2.Progr.SSH import SSH, ArpStatus

import requests

class OpenRGB(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.OpenRGB, room)
    
    def auth(self, ip_address, port, program_name):
        self.ip_address = ip_address
        self.port = port
        self.program_name = program_name
        super().auth(ip_address = ip_address, port = port, program_name = program_name)
    def is_my_device(self, ip_address):
        return False
    def create_noip_devices(self): 
        devices = []
