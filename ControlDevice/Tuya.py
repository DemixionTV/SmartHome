from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
import tinytuya

device_switches = {
    'USB Smart Adapter':1,
    'New-PC-Button': 2,
    'Умный светильник': 20
}



class TuyaCD(ControlDevice):
    def __init__(self, tuya_device, product_name):
        super().__init__(locals().copy())
        self.manufacturer_type = ManufacturerType.Tuya
        self.tuya_device = tuya_device
        self.ip_address = tuya_device['ip']
        self.device_name = tuya_device['name']
        self.mac_address = tuya_device['mac'].upper().replace('-',':')
        self.version = tuya_device['version']
        if product_name == 'Умный светильник':
            self.device_type = DeviceType.Lamp
            self.device = tinytuya.BulbDevice(dev_id=tuya_device['id'],address=self.ip_address,local_key=tuya_device['key'],version=tuya_device['version'])
            self.toggle_ability(DeviceAbility.TurnOn)
            self.toggle_ability(DeviceAbility.TurnOff)
            self.toggle_ability(DeviceAbility.GetDevicePower)            
            if self.device.has_colour:
                self.toggle_ability(DeviceAbility.SetColor,colors = None)
                self.toggle_ability(DeviceAbility.GetColor)
                self.toggle_ability(DeviceAbility.GetLeds, led_names = [self.device_name])
            if self.device.has_brightness:
                self.toggle_ability(DeviceAbility.SetBrightness,min_brightness = {self.device_name:0},max_brightness = {self.device_name:1000})
                self.toggle_ability(DeviceAbility.GetBrightness)
                self.toggle_ability(DeviceAbility.GetLeds, led_names = [self.device_name])
#                print(tuya_device, self.device.DPS_INDEX_BRIGHTNESS, self.device.DPS_INDEX_ON, self.device.detect_available_dps(), self.device.set_brightness_percentage)
#                self.update_ability(DeviceAbility.Brightness, [0,1000])
            if self.device.has_colourtemp:
                self.toggle_ability(DeviceAbility.SetColorTemperature,min_temperature = 2700,max_temperature = 5700)
                self.toggle_ability(DeviceAbility.GetLeds, led_names = [self.device_name])
                self.min_temp = 2700
                self.max_temp = 5700
        elif product_name == 'New-PC-Button':
            self.device_type = DeviceType.PC_Power_Button
            self.device = tinytuya.OutletDevice(dev_id=tuya_device['id'],address=self.ip_address,local_key=tuya_device['key'],version=tuya_device['version'])
            self.toggle_ability(DeviceAbility.Press)
        elif product_name == 'USB Smart Adapter':
            self.device_type = DeviceType.USBPlug
            self.device = tinytuya.OutletDevice(dev_id=tuya_device['id'],address=self.ip_address,local_key=tuya_device['key'],version=tuya_device['version'])
            self.toggle_ability(DeviceAbility.TurnOn)
            self.toggle_ability(DeviceAbility.TurnOff)
            self.toggle_ability(DeviceAbility.GetDevicePower)
        self.switch = device_switches[product_name]
    def get_device_name(self):
        return self.device_name
    def off(self):
        self.device.turn_off(switch=self.switch)
    def on(self):
        self.device.turn_on(switch=self.switch)
    def get_power(self):
        dev_status = self.device.status()
        if dev_status != None and 'dps' in dev_status and str(self.switch) in dev_status['dps']:
            return dev_status['dps'][str(self.switch)] 
        else: 
            return False
    def set_color(self, led_name, red, green, blue):
        if red == 0 and green == 0 and blue == 0:
            self.off()
        else:
            self.device.set_colour(red, green, blue)
    def get_color(self):
        if self.get_power():
            return {self.device_name:self.device.colour_rgb()}
        else:
            return {self.device_name:(0,0,0)}

    def set_color_temperature(self, led_name, color_temperature):
        new_ct = (color_temperature - self.min_temp) / (self.max_temp - self.min_temp)
#        print(new_ct * 1000.0)
        self.device.set_colourtemp(int(new_ct * 1000.0))
    
    def get_color_temperature(self):
        if not self.get_power():
            return {self.device_name:0}
        return {self.device_name:self.device.colourtemp()}
    def press(self):
        self.on()
    
    def set_brightness(self, led_name, brightness):
        self.device.turn_on(self.switch)
        self.device.set_brightness(brightness, nowait=True)
    def get_brightness(self):
        if not self.get_power():
            return {self.device_name:0}
        return {self.device_name:int(self.device.brightness() / 10.0)}
    def get_control_device(self):
        return f'Tuya v{self.version}'
