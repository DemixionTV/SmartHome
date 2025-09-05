
from enum import Enum, IntEnum, auto



class ManufacturerType(Enum):
    TP_Link_Tapo = 'TP-Link Tapo'
    TP_Link_Tapo_Child = 'TP-Link Tapo Child'
    Tuya = 'Tuya'
    OpenWRT = 'OpenWRT'
    Xigmanas = 'Xigmanas'
    Yeelight = 'Yeelight'
    GPIO = 'GPIO'
    Discord = 'Discord'
    OpenRGB = 'OpenRGB'
    OpenWeather = 'OpenWeather'


class DeviceType(IntEnum):
    Lamp = auto()
    Plug = auto()
    Hub = auto()
    USBPlug = auto()
    PC_Power_Button = auto()
    Router = auto()
    Nas_Server = auto()
    Discord_Bot = auto()
    Motion_Sensor = auto()
    Humidity_Temperature_Sensor = auto()


class DeviceAbility(IntEnum):
    ChildrenDevices = auto()
    TurnOn = auto()
    TurnOff = auto()
    GetDevicePower = auto()
    GetOnlineDevices = auto()
    OnlineDeviceUpdate = auto()
    GetLeds = auto()
    SetColor = auto()
    GetColor = auto()
    GetBrightness = auto()
    SetBrightness = auto()
    SetColorTemperature = auto()
    GetColorTemperature = auto()
    BotCommand = auto()
    Press = auto()
    GetPowerUsage = auto()
    GetPowerSavings = auto()
    GetUsageTime = auto()
    GetCurrentPower = auto()
    GetHumidity = auto()
    GetTemperature = auto()
    DetectMotion = auto()
    SMBShares = auto()
    GetServices = auto()
    ToggleService = auto()
    RestartService = auto()
    GetServiceStatus = auto()
