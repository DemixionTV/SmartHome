from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice

from Diamon2.SmartHome3.Enum import DeviceAbility, DeviceType

from Diamon2.Progr.Net import NetDevice
from Diamon2.Progr.Colors import bcolors

from typing import List


class SmartDevice:
    def __init__(self, control_device:ControlDevice, manufacturer):
        self.device_type:DeviceType = control_device.get_device_type()
        self.device_name = control_device.get_device_name()
        self.control_device = control_device
        self.manufacturer = manufacturer
        self.control_device.manufacturer = self.manufacturer
        self.control_device.room = self.manufacturer.room


    def __repr__(self):
        r = f'{bcolors.OKCYAN}{self.device_name}{bcolors.ENDC} | {bcolors.WARNING}{self.device_type.name}{bcolors.ENDC}'
        if self.get_ip_address():
            r += f' | {bcolors.OKGREEN}{self.get_ip_address()}{bcolors.ENDC}'
        if self.get_mac_address():
            r += f' | {bcolors.OKBLUE}{self.get_mac_address()}{bcolors.ENDC}'
        return r.strip()

    @staticmethod
    def use_control_device(ability:DeviceAbility):
        def wrapper(func):
            def inner(self, *args, **kwargs):
                if self.control_device.has_ability(ability):
                    return getattr(self.control_device, func.__name__)(*args, **kwargs)
#                func(self, *args, **kwargs)
#                self.control_device.on()
            inner.device_ability = ability
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
    
    

    @use_control_device(DeviceAbility.ChildrenDevices)
    def create_children_devices(self):
        pass

    @use_control_device(DeviceAbility.TurnOn)
    def on(self):
        pass
    @use_control_device(DeviceAbility.TurnOff)
    def off(self):
        pass
    @use_control_device(DeviceAbility.GetDevicePower)
    def get_power(self):
        pass
    @use_control_device(DeviceAbility.GetOnlineDevices)
    def get_online_devices(self) -> List[NetDevice]:
        pass
    @use_control_device(DeviceAbility.GetColorTemperature)
    def get_color_temperature(self):
        pass
    @use_control_device(DeviceAbility.SetColorTemperature)
    def set_color_temperature(self, color_temperature):
        pass
    @use_control_device(DeviceAbility.SetColor)
    def set_color(self, red, green, blue):
        pass
    @use_control_device(DeviceAbility.GetColor)
    def get_color(self):
        pass
    @use_control_device(DeviceAbility.Press)
    def press(self):
        pass

    