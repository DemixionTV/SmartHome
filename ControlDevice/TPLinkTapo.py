from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from Diamon2.SmartHome3.ControlDevice.TPLinkTapoChildCD import TPLinkTapoChildCD
from tapo.responses import KE100Result, S200BResult, T100Result, T110Result, T300Result, T31XResult

import asyncio
from tapo import ApiClient
import base64
from Diamon2.Progr.Colors import rgb_to_hsl, hsl_to_rgb

class TapoCD(ControlDevice):
    def __init__(self, login, password, ip_address):
        super().__init__(locals().copy())
        self.login = login
        self.password = password
        self.ip_address = ip_address
        self.client = None
        self.device = None
        self.manufacturer_type = ManufacturerType.TP_Link_Tapo
        self.auth()
        
    async def _auth(self):
        try:
            self.client = ApiClient(self.login,self.password)
            device = await self.client.generic_device(self.ip_address)
            device_info = await device.get_device_info_json()
            self.mac_address = device_info['mac'].upper().replace('-',':')
            self.device_name = base64.b64decode(device_info['nickname']).decode('utf-8')
            if device_info['model'] == 'L530':
                self.device = await self.client.l530(self.ip_address)
                self.device_type = DeviceType.Lamp
                self.toggle_ability(DeviceAbility.TurnOn)
                self.toggle_ability(DeviceAbility.TurnOff)
                self.toggle_ability(DeviceAbility.GetDevicePower)
                self.toggle_ability(DeviceAbility.SetColorTemperature,min_temperature = device_info['color_temp_range'][0], max_temperature = device_info['color_temp_range'][1])
                self.toggle_ability(DeviceAbility.GetColorTemperature)
                self.toggle_ability(DeviceAbility.SetColor, colors = None)
                self.toggle_ability(DeviceAbility.GetColor)
            elif device_info['model'] == 'P110':
                self.device = await self.client.p110(self.ip_address)
                self.device_type = DeviceType.Plug
                self.toggle_ability(DeviceAbility.TurnOn)
                self.toggle_ability(DeviceAbility.TurnOff)
                self.toggle_ability(DeviceAbility.GetDevicePower)
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
    
    def set_color_temperature(self, color_temperature):
        asyncio.run(self._set_color_temperature(color_temperature))
    
    def get_color_temperature(self):
        return self._get_device_info()['color_temp']
    
    async def _set_color(self,r,g,b):
        if int(r) == 0 and int(g) == 0 and int(b) == 0:
            await self.device.off()
        else:
            h,s,l = rgb_to_hsl([int(r),int(g),int(b)])
            await self.device.set().hue_saturation(h, s).brightness(int(l)).send(self.device)

    def set_color(self, red,green,blue):
        asyncio.run(self._set_color(red,green,blue))

    def get_color(self):
        if self.get_power():
            device_info = self._get_device_info()
            h = device_info['hue']
            s = device_info['saturation']
            l = device_info['brightness']
            r,g,b = hsl_to_rgb([h,s,l])
            return (r,g,b)
        else: 
            return (0,0,0) 
        
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

