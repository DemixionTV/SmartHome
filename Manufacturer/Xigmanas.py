from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType
from Diamon2.SmartHome3.ControlDevice.Xigmanas import XigmanasCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from Diamon2.Progr.SSH import SSH, ArpStatus


from Diamon2.Progr.Net import checkPort

class Xigmanas(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.Xigmanas, room)
    
    def auth(self, login, password, port):
        self.login = login
        self.password = password
        self.port = port
        super().auth(login = login,password = password)

    def is_my_device(self, ip_address):
        try:
            if checkPort(ip_address,22) and checkPort(ip_address,445):
                try:
                    client = SSH()
                    client.connect(ip_address,self.port,self.login,self.password)
                    return True
                except:
                    return False
            else:
                return False
        except Exception as e:
            return False
    def create_device(self, ip_address):
        control_device = XigmanasCD(ip_address, self.login, self.password, self.port)
        self.registered_devices.append(ip_address)
        return SmartDevice(control_device,self)
