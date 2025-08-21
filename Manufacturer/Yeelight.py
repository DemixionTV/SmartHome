from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType
from Diamon2.SmartHome3.ControlDevice.Yeelight import YeelightCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice
import yeelight

class Yeelight(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.Yeelight, room)
    def is_my_device(self, ip_address):
        try:
            b = yeelight.Bulb(ip_address)
            info = b.get_model_specs()
            info = b.get_capabilities()['model']
            return True
        except:
            return False
    
    def create_device(self, ip_address):
        control_device = YeelightCD(ip_address)
        self.registered_devices.append(ip_address)
        return SmartDevice(control_device, self)
    
    def auth(self, **args):
        return super().auth(**args)