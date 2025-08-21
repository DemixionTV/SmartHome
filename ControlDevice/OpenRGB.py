from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.Progr.SSH import SSH, ArpStatus
from Diamon2.Progr.Net import NetDevice

from openrgb.utils import RGBColor
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType as OpenRGBDeviceType, ModeFlags

class OpenRGBCD(ControlDevice):
    def __init__(self, ip_address, login, password, port):
        super().__init__(locals().copy())
        