from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType

import yeelight
from Diamon2.Progr.Text import translit
from Diamon2.Progr.Net import get_mac_by_ip
from Diamon2.Progr.Colors import kelvin_to_rgb

device_switches = {
    'USB Smart Adapter':1,
    'New-PC-Button': 2,
    'Умный светильник': 20
}



class YeelightCD(ControlDevice):
    def __init__(self, ip_address):
        super().__init__(locals().copy())
        self.manufacturer_type = ManufacturerType.Yeelight
        self.device = yeelight.Bulb(ip_address)
        self.device_type = DeviceType.Lamp
        self.device_name = self.get_device_name()
        self.toggle_ability(DeviceAbility.GetLeds,led_names = [self.device_name])
        if 'set_power' in self.device.get_capabilities()['support']:
            self.toggle_ability(DeviceAbility.TurnOn)
            self.toggle_ability(DeviceAbility.TurnOff)
            self.toggle_ability(DeviceAbility.GetDevicePower)
        if 'set_bright' in self.device.get_capabilities()['support']:
            self.toggle_ability(DeviceAbility.SetBrightness, min_brightness = {self.device_name:0}, max_brightness = {self.device_name:100})
            self.toggle_ability(DeviceAbility.GetBrightness)
        if 'color_temp' in self.device.get_model_specs().keys() and self.device.get_model_specs()['color_temp'].get('min') != None and self.device.get_model_specs()['color_temp'].get('max') != None:
            self.toggle_ability(DeviceAbility.SetColorTemperature, min_temperature = self.device.get_model_specs()['color_temp'].get('min'), max_temperature = self.device.get_model_specs()['color_temp'].get('max'))
            self.toggle_ability(DeviceAbility.GetColorTemperature)
            self.toggle_ability(DeviceAbility.GetColor)
        self.mac_address = get_mac_by_ip(ip_address)
        self.ip_address = ip_address

    def get_control_device(self):
        return f'Yeelight {self.device.model}'

    def get_device_name(self):
        return translit(f'{self.device.get_capabilities()["model"]} id{self.device.get_capabilities()["id"]}')

    def on(self):
        self.device.turn_on()

    def off(self):
        self.device.turn_off()

    def get_power(self):
        return self.device.get_properties()['power'] == 'on'
    
    def get_color_temperature(self):
        if not self.get_power():
            return{self.device_name:0}
        return {self.device_name:int(self.device.get_properties()['ct'])}
    
    def set_color_temperature(self, led_name, color_temperature:int):
        self.device.turn_on()
        return self.device.set_color_temp(color_temperature)
    
    def get_brightness(self):
        if not self.get_power():
            return{self.device_name:0}
        return {self.device_name:int(self.device.get_properties()['current_brightness'])}
    def set_brightness(self, led_name, brightness:int):
        if brightness == 0:
            self.off()
        else:
            self.device.turn_on()
            self.device.set_brightness(brightness)
    def get_color(self):
        if not self.get_power():
            return {self.device_name:(0,0,0)}
        return {self.device_name:kelvin_to_rgb(self.get_color_temperature()[self.device_name])}