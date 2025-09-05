from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from tapo.responses import KE100Result, S200BResult, T100Result, T110Result, T300Result, T31XResult

import asyncio
from tapo import ApiClient
import base64
from Diamon2.Progr.Colors import rgb_to_hsl, hsl_to_rgb
import datetime

class TPLinkTapoChildCD(ControlDevice):
    def __init__(self, device, device_info, child):
        super().__init__(locals().copy(), no_save=True)
        self.device = device
        self.child = child
#        self.client = None
#        self.device = None
        self.manufacturer_type = ManufacturerType.TP_Link_Tapo_Child
        self.device_name = base64.b64decode(device_info['nickname']).decode('utf-8')
        self.control_device_name = f'TP-Link {device_info["model"]}'
        if device_info['model'] == 'T100':
            self.toggle_ability(DeviceAbility.DetectMotion)
        elif device_info['model'] == 'T315':
            self.toggle_ability(DeviceAbility.GetHumidity)
            self.toggle_ability(DeviceAbility.GetTemperature)


    async def _get_device_info(self):
        device_info = await self.device.get_device_info_json()
        return device_info
    
    def get_device_info(self):
        return asyncio.run(self._get_device_info())

    def get_device_name(self):
        return self.device_name
    
    def get_control_device(self):
        return self.control_device_name
    

    async def _get_ht_records(self):
        temperature_humidity_records = await self.device.get_temperature_humidity_records()
        return temperature_humidity_records

    def get_temperature(self):
        return self.get_device_info()['current_temp']
#        last_temp_info = [record.to_dict() for record in asyncio.run(self._get_ht_records()).records][-1]
#        return round(float(last_temp_info['temperature']),1)
    
    def get_humidity(self):
        return self.get_device_info()['current_humidity']
#        last_temp_info = [record.to_dict() for record in asyncio.run(self._get_ht_records()).records][-1]
#        return int(last_temp_info['humidity'])
    
    async def get_trigger_logs(self):
        return await self.device.get_trigger_logs(1,0)

    def detect_motion(self):
        logs = [log.to_dict() for log in asyncio.run(self.get_trigger_logs()).logs][0]
        return datetime.datetime.fromtimestamp(logs['timestamp'])
    
