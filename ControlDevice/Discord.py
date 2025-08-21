from Diamon2.SmartHome3.ControlDevice.ControlDevice import ControlDevice
from Diamon2.SmartHome3.Enum import DeviceType, DeviceAbility, ManufacturerType
from Diamon2.Progr.SSH import SSH, ArpStatus
from Diamon2.Progr.Net import NetDevice
import time

import discord
from discord.ext import commands

from threading import Thread


class DiscordCD(ControlDevice):
    def __init__(self, api_key):
        super().__init__(locals().copy())
        intents = discord.Intents.default()
        intents.voice_states = True  # обязательно, если ты работаешь с голосом
        intents.message_content = True
        self.client = commands.Bot(command_prefix='?',intents = intents)
        self.register_events()
        self.api_key = api_key
        self.nickname = None
        self.name = f'Discord bot'
        self.device_type = DeviceType.Discord_Bot
        self.manufacturer_type = ManufacturerType.Discord
        self.ready = False
        th = Thread(target=self.run,daemon=True)
        th.start()
        while not self.ready:
            time.sleep(0.01)
    def register_events(self):
        @self.client.event
        async def on_ready():
#            print('Bot is ready.', self.client.user.name)
            self.nickname = self.client.user.name
            self.name = f'Discord bot {self.nickname}'
            self.ready = True
        @self.client.event
        async def on_command_error(ctx:commands.Context, error):
            self.room.on_bot_command(self.name,ctx.invoked_with, ctx.message.content, ctx.guild.id, ctx.author.id)
#            print(ctx.__dict__, error.__dict__)
#            print(ctx.invoked_with, ctx.message.content)
    def run(self):
        self.client.run(self.api_key)
    def get_device_name(self):
        return f'Discord bot {self.nickname}'
    def unregister(self):
        self.client.close()
