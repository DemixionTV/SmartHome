from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from Diamon2.SmartHome3.ControlDevice.TPLinkTapoChildCD import TPLinkTapoChildCD
from tapo.responses import KE100Result, S200BResult, T100Result, T110Result, T300Result, T31XResult

import asyncio
from tapo import ApiClient
import base64
from Diamon2.Progr.Colors import rgb_to_hsl, hsl_to_rgb, hsv_to_rgb, kelvin_to_rgb

class TapoCD(ControlDevice):
    def __init__(self, login, password, ip_address):
        super().__init__(locals().copy())
        self.login = login
        self.password = password
        self.ip_address = ip_address
        self.client = None
        self.device = None
        self.control_device_name = None
        self.manufacturer_type = ManufacturerType.TP_Link_Tapo
        self.auth()
        
    async def _auth(self):
        try:
            self.client = ApiClient(self.login,self.password)
            device = await self.client.generic_device(self.ip_address)
            device_info = await device.get_device_info_json()
            self.mac_address = device_info['mac'].upper().replace('-',':')
            self.device_name = base64.b64decode(device_info['nickname']).decode('utf-8')
            self.control_device_name = f'TP-Link {device_info["model"]}'
            if device_info['model'] == 'L530':
                self.device = await self.client.l530(self.ip_address)
                self.device_type = DeviceType.Lamp
                self.toggle_ability(DeviceAbility.TurnOn)
                self.toggle_ability(DeviceAbility.TurnOff)
                self.toggle_ability(DeviceAbility.GetDevicePower)
                self.toggle_ability(DeviceAbility.SetColorTemperature,min_temperature = device_info['color_temp_range'][0], max_temperature = device_info['color_temp_range'][1])
                self.toggle_ability(DeviceAbility.GetColorTemperature)
                self.toggle_ability(DeviceAbility.SetBrightness, min_brightness = {self.device_name:0}, max_brightness = {self.device_name:100})
                self.toggle_ability(DeviceAbility.GetBrightness)
                self.toggle_ability(DeviceAbility.SetColor, colors = None)
                self.toggle_ability(DeviceAbility.GetColor)
                self.toggle_ability(DeviceAbility.GetLeds, led_names = [self.device_name])
                self.toggle_ability(DeviceAbility.GetPowerSavings)
                self.toggle_ability(DeviceAbility.GetPowerUsage)
                self.toggle_ability(DeviceAbility.GetUsageTime)
            elif device_info['model'] == 'P110':
                self.device = await self.client.p110(self.ip_address)
                self.device_type = DeviceType.Plug
                self.toggle_ability(DeviceAbility.TurnOn)
                self.toggle_ability(DeviceAbility.TurnOff)
                self.toggle_ability(DeviceAbility.GetDevicePower)
                self.toggle_ability(DeviceAbility.GetPowerUsage)
                self.toggle_ability(DeviceAbility.GetUsageTime)
                self.toggle_ability(DeviceAbility.GetCurrentPower)
            elif device_info['model'] == 'H100':
                self.device = await self.client.h100(self.ip_address)
                self.toggle_ability(DeviceAbility.ChildrenDevices)
                self.device_type = DeviceType.Hub
        except:
            pass

    def auth(self):
        asyncio.run(self._auth())

    async def _on(self):
        if self.device:
            await self.device.on()
    
    def on(self):
        asyncio.run(self._on())
    
    async def _off(self):
        if self.device:
            await self.device.off()
    
    def off(self):
        asyncio.run(self._off())

    def get_device_name(self):
        return self.device_name
    def _get_device_info(self):
        return asyncio.run(self.device.get_device_info_json())
    def get_power(self):
        return self._get_device_info()['device_on']
    
    
    async def _set_color_temperature(self,ct):
        await self.device.set_color_temperature(ct)
    
    def set_color_temperature(self, led_name, color_temperature):
        asyncio.run(self._set_color_temperature(color_temperature))
    
    def get_color_temperature(self):
        if not self.get_power():
            return {self.device_name:0}
        return {self.device_name:self._get_device_info()['color_temp']}
    def get_brightness(self):
        if not self.get_power():
            return {self.device_name:0}
        return {self.device_name:self._get_device_info()["brightness"]}
    
    async def _set_brightness(self, b):
        if b > 0:
            await self.device.set_brightness(b)
        else:
            await self.device.off()
    
    def set_brightness(self, led_name,brightness):
        asyncio.run(self._set_brightness(brightness))


    async def _set_color(self,r,g,b):
        if int(r) == 0 and int(g) == 0 and int(b) == 0:
            await self.device.off()
        else:
            h,s,l = rgb_to_hsl([int(r),int(g),int(b)])
            await self.device.set().hue_saturation(h, s).brightness(int(l)).send(self.device)

    def set_color(self, led_name,red,green,blue):
        asyncio.run(self._set_color(red,green,blue))

    def get_color(self):
        if self.get_power():
            device_info = self._get_device_info()
            if device_info['color_temp'] != 0:
                return {self.device_name:kelvin_to_rgb(device_info['color_temp'])}
            h = device_info['hue']
            s = device_info['saturation']
#            l = device_info['brightness']
            r,g,b = hsv_to_rgb(h,s/100.0,1.0)
            return {self.device_name:(r,g,b)}
        else: 
            return {self.device_name:(0,0,0)} 
        
    async def _create_children_devices(self):
        child_device_list = await self.device.get_child_device_list()
        devices = []
        for child in child_device_list:
            if isinstance(child, T31XResult):
                t31x = await self.device.t315(device_id=child.device_id)
                device_info = await t31x.get_device_info_json()
                control_device = TPLinkTapoChildCD(t31x,device_info,child)
#                control_device.update_ability(DeviceAbility.Temperature,True)
#                control_device.update_ability(DeviceAbility.Humidity,True)
                dev = SmartDevice(control_device,self.manufacturer)
                dev.device_type = DeviceType.Humidity_Temperature_Sensor
                devices.append(dev)
            elif isinstance(child, T100Result):
                t100 = await self.device.t100(device_id=child.device_id)
                device_info = await t100.get_device_info_json()
                control_device = TPLinkTapoChildCD(t100,device_info,child)
#                control_device.update_ability(DeviceAbility.Motion,True)
                dev = SmartDevice(control_device,self.manufacturer)
                dev.device_type = DeviceType.Motion_Sensor
                devices.append(dev)
            
        return devices
    
    def create_children_devices(self):
        return asyncio.run(self._create_children_devices())
    
    async def _get_device_usage(self):
        device_usage_ = await self.device.get_device_usage()
        device_usage = device_usage_.to_dict()
        return device_usage
    
    def get_device_usage(self):
        return asyncio.run(self._get_device_usage())
        
    
    async def _get_current_power(self):
        energy_usage_ = await self.device.get_current_power()
        energy_usage = energy_usage_.to_dict()
        return energy_usage["current_power"]
    
    def get_current_power(self):
        return asyncio.run(self._get_current_power())
    
    def get_power_savings(self):
        device_usage = self.get_device_usage()
        usage = {
            "1 day":device_usage["saved_power"]["today"] / 1000.0,
            "7 days":device_usage["saved_power"]["past7"] / 1000.0,
            "30 days":device_usage["saved_power"]["past30"] / 1000.0
            }
        return usage
    def get_power_usage(self):
        device_usage = self.get_device_usage()
        usage = {
            "1 day":device_usage["power_usage"]["today"] / 1000.0,
            "7 days":device_usage["power_usage"]["past7"] / 1000.0,
            "30 days":device_usage["power_usage"]["past30"] / 1000.0
        }
        return usage
    
    def get_usage_time(self):
        device_usage = self.get_device_usage()
        usage = {
            "1 day":device_usage["time_usage"]["today"] / 60.0,
            "7 days":device_usage["time_usage"]["past7"] / 60.0,
            "30 days":device_usage["time_usage"]["past30"] / 60.0
            }
        return usage
    def get_control_device(self):
        return self.control_device_name