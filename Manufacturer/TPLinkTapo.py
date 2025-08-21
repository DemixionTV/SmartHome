from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType
from Diamon2.SmartHome3.ControlDevice.TPLinkTapo import TapoCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from tapo import ApiClient
import asyncio

class TPLinkTapo(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.TP_Link_Tapo, room)

    def auth(self, login, password):
        self.login = login
        self.password = password
        super().auth(login = login, password = password)


    async def _is_my_device(self, ip_address):
        try:
            client = ApiClient(self.login, self.password)
            dev = await client.generic_device(ip_address)
            device_info = await dev.get_device_info_json()
            del client
            return True
        except Exception as e:
            return False

    def is_my_device(self, ip_address):
        return asyncio.run(self._is_my_device(ip_address))
    
    def create_device(self, ip_address) -> SmartDevice:
        self.registered_devices.append(ip_address)
        return SmartDevice(TapoCD(self.login, self.password, ip_address),self)
    

        