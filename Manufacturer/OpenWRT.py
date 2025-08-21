from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType, DeviceAbility
from Diamon2.SmartHome3.ControlDevice.OpenWRT import OpenWRTCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from Diamon2.Progr.Net import getOS, getSubnet, checkPort
from Diamon2.Progr.SSH import SSH, ArpStatus

import requests

class OpenWRT(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.OpenWRT, room)
    
    def auth(self, login, password, port):
        self.login = login
        self.password = password
        self.port = port
        super().auth(login = login, password = password, port = port)
    def is_my_device(self, ip_address):
        if getSubnet(ip_address) in getSubnet(self.registered_devices):
            return False
        try:
            if checkPort(ip_address,22):
                try:
                    client = SSH()
                    client.connect(ip_address,self.port,self.login,self.password)
                except:
                    return False
                response = requests.get(f"http://{ip_address}", timeout=2)
                if "OpenWrt" in response.text or "LuCI" in response.text:
                    return True
        except requests.exceptions.RequestException:
            pass
        return False
    def create_device(self, ip_address):
        control_device = OpenWRTCD(ip_address, self.login, self.password, self.port)
        self.registered_devices.append(ip_address)
        return SmartDevice(control_device,self)