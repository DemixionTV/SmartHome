from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.SmartHome3.SmartDevice import SmartDevice
from Diamon2.Progr.Text import translit
import requests
import datetime

class OpenWeatherCD(ControlDevice):
    def __init__(self,token):
        super().__init__(locals().copy())
        my_city = requests.get('http://ipinfo.io/json').json()['city']
        self.url = 'https://api.openweathermap.org/data/2.5/weather?q='+my_city+'&units=metric&lang=ru&appid=' + token
        self.last_request = None
        self.last_info = None
        self.city_name = self.get_info()['name']
        self.device_type = DeviceType.Humidity_Temperature_Sensor
        self.toggle_ability(DeviceAbility.GetHumidity)
        self.toggle_ability(DeviceAbility.GetTemperature)
#        print(self.get_info())
        
    def get_info(self):
        if self.last_request == None or self.last_info == None or datetime.datetime.now() > self.last_request + datetime.timedelta(minutes = 1):
            self.last_info = requests.get(self.url).json()
            self.last_request = datetime.datetime.now()
        return self.last_info
    
    
    def get_control_device(self):
        return f'OpenWeather {self.city_name}'
    def get_device_name(self):
        return f'Температура и влажность в {self.city_name}'
    
    def get_temperature(self):
        return self.get_info()['main']['temp']
    def get_humidity(self):
        return self.get_info()['main']['humidity']
    