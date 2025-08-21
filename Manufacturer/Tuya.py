from Diamon2.SmartHome3.Manufacturer.Manufacturer import Manufacturer
from Diamon2.SmartHome3.Enum import ManufacturerType, DeviceType
from Diamon2.SmartHome3.ControlDevice.Tuya import TuyaCD
from Diamon2.SmartHome3.SmartDevice import SmartDevice
import os
import tinytuya
from tinytuya.wizard import wizard
import json

class Tuya(Manufacturer):
    def __init__(self, room):
        super().__init__(ManufacturerType.Tuya, room)
    
    def auth(self, api_key, secret_key):
        super().auth(api_key = api_key, secret_key = secret_key)
        self.api_key = api_key
        self.secret_key = secret_key
        if not os.path.exists('tuya-raw.json') or not os.path.exists('snapshot.json'):
            try:
                wizard(credentials={'apiKey':self.api_key,'apiSecret':self.secret_key,'apiRegion':'EU'},assume_yes=True)
            except Exception as e:
                pass
            try:
                tinytuya.scan()
            except Exception as e:
                pass
        with open('tuya-raw.json') as f:
            self.tuya_raw = json.load(f)['result']
        with open('snapshot.json') as f:
            devices = json.load(f)['devices']
            self.tuya_devices = {}
            for dev in devices:
                self.tuya_devices[dev['ip']] = {}
                self.tuya_devices[dev['ip']]['ip'] = dev['ip']
                self.tuya_devices[dev['ip']]['id'] = dev['id']
                self.tuya_devices[dev['ip']]['version'] = dev['ver']
                self.tuya_devices[dev['ip']]['key'] = dev['key']
                self.tuya_devices[dev['ip']]['name'] = dev['name']
                self.tuya_devices[dev['ip']]['mac'] = dev['mac']
    def is_my_device(self, ip_address):
        return ip_address in self.tuya_devices
    
    def create_device(self, ip_address):
        product_name = None
        for tr in self.tuya_raw:
            if tr['id'] == self.tuya_devices[ip_address]['id']:
                product_name = tr['product_name']
        control_device = TuyaCD(self.tuya_devices[ip_address], product_name)
        self.registered_devices.append(ip_address)
        return SmartDevice(control_device, self)