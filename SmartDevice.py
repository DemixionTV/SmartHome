from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice

from Diamon2.SmartHome3.Enum import DeviceAbility, DeviceType

from Diamon2.Progr.Net import NetDevice
from Diamon2.Progr.Colors import bcolors

from typing import List, Tuple, Annotated, Union


class SmartDevice:
    def __init__(self, control_device:ControlDevice, manufacturer):
        self.device_type:DeviceType = control_device.get_device_type()
        self.device_name = control_device.get_device_name()
        self.control_device:ControlDevice = control_device
        self.manufacturer = manufacturer
        self.control_device.manufacturer = self.manufacturer
        self.database_id = None
        try:
            self.control_device.room = self.manufacturer.room
        except:
            pass

    def __repr__(self):
        r = f'{bcolors.OKCYAN}{self.device_name}{bcolors.ENDC} | {bcolors.WARNING}{self.device_type.name}{bcolors.ENDC}'
        if self.get_ip_address():
            r += f' | {bcolors.OKGREEN}{self.get_ip_address()}{bcolors.ENDC}'
        if self.get_mac_address():
            r += f' | {bcolors.OKBLUE}{self.get_mac_address()}{bcolors.ENDC}'
        return r.strip()

    @staticmethod
    def use_control_device(ability:DeviceAbility, require_unlock = False):
        def wrapper(func):
            def inner(self, *args, **kwargs):
                if self.control_device.has_ability(ability):
                    if require_unlock and self.control_device.is_locked():
                        return None
                    return getattr(self.control_device, func.__name__)(*args, **kwargs)
#                func(self, *args, **kwargs)
#                self.control_device.on()
            inner.device_ability = ability
            inner.main_func = func
            return inner
        return wrapper
    
    def get_ip_address(self):
        return self.control_device.ip_address
    
    def get_mac_address(self):
        return self.control_device.mac_address
    
    def get_device_type(self):
        return self.device_type
    def is_online(self):
        return self.control_device.is_online()
    
    def on_register(self, register_info = None):
        self.control_device.on_register(register_info)
    
    def get_abilities(self):
        return self.control_device.get_abilities()
    
    def has_ability(self, ability:DeviceAbility):
        return self.control_device.has_ability(ability)
    
    def lock_device(self,lock:bool):
        self.control_device.lock(lock)
    def is_locked(self):
        return self.control_device.is_locked()
    def get_control_device(self):
        return self.control_device.get_control_device()

    
    

    @use_control_device(DeviceAbility.ChildrenDevices)
    def create_children_devices(self):
        pass

    @use_control_device(DeviceAbility.TurnOn, require_unlock = True)
    def on(self):
        pass
    @use_control_device(DeviceAbility.TurnOff, require_unlock = True)
    def off(self):
        pass
    @use_control_device(DeviceAbility.GetDevicePower)
    def get_power(self) -> Annotated[bool,"Device Power"]:
        pass
    @use_control_device(DeviceAbility.GetOnlineDevices)
    def get_online_devices(self) -> Annotated[List[NetDevice],"Online Devices"]:
        pass
    @use_control_device(DeviceAbility.GetColorTemperature)
    def get_color_temperature(self) -> Annotated[int,"Color Temperature"]:
        pass
    @use_control_device(DeviceAbility.SetColorTemperature, require_unlock = True)
    def set_color_temperature(self, led_name, color_temperature):
        pass
    @use_control_device(DeviceAbility.SetColor, require_unlock = True)
    def set_color(self, led_name, red, green, blue):
        pass
    @use_control_device(DeviceAbility.GetColor)
    def get_color(self) -> Tuple[Annotated[int,"red"],Annotated[int, "green"],Annotated[int, "blue"]]:
        pass
    @use_control_device(DeviceAbility.Press, require_unlock = True)
    def press(self):
        pass
    @use_control_device(DeviceAbility.OnlineDeviceUpdate)
    def online_device_update(self,target_ip_address, port = 11511):
        pass
    @use_control_device(DeviceAbility.GetBrightness)
    def get_brightness(self) -> Annotated[int, "brightness"]:
        pass
    @use_control_device(DeviceAbility.SetBrightness, require_unlock = True)
    def set_brightness(self, led_name, brightness):
        pass
    @use_control_device(DeviceAbility.GetPowerSavings)
    def get_power_savings(self) -> Annotated[dict, "Power savings"]:
        pass
    @use_control_device(DeviceAbility.GetPowerUsage)
    def get_power_usage(self) -> Annotated[dict, "Power Usage"]:
        pass
    @use_control_device(DeviceAbility.GetUsageTime)
    def get_usage_time(self) -> Annotated[dict, "Usage Time"]:
        pass
    @use_control_device(DeviceAbility.GetCurrentPower)
    def get_current_power(self) -> Annotated[float,"Current Power"]:
        pass
    @use_control_device(DeviceAbility.GetHumidity)
    def get_humidity(self) -> Annotated[float, "Humidity"]:
        pass
    @use_control_device(DeviceAbility.GetTemperature)
    def get_temperature(self) -> Annotated[float, "Temperature"]:
        pass
    @use_control_device(DeviceAbility.DetectMotion)
    def detect_motion(self):
        pass
    @use_control_device(DeviceAbility.SMBShares)
    def get_smb_shares(self) -> Annotated[dict, "Smb Shares"]:
        pass
    @use_control_device(DeviceAbility.ToggleService)
    def toggle_service(self, service_name:str, state:bool):
        pass
    @use_control_device(DeviceAbility.GetServices)
    def get_services(self) -> Annotated[List[str], "Services"]:
        pass
    @use_control_device(DeviceAbility.RestartService)
    def restart_service(self, service_name):
        pass
    @use_control_device(DeviceAbility.GetServiceStatus)
    def get_service_status(self, service_name) -> Annotated[str, "Service status"]:
        pass


    