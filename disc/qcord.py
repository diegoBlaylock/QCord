'''
Created on Oct 3, 2022

@author: diego
'''

import discord.client
import discord.app_commands as commands
import asyncio
from importlib import reload
from importlib.util import find_spec
import importlib.util as util
import sys
from inspect import iscoroutinefunction
import logger
from discord.channel import TextChannel
from discord.guild import Guild

class Port():
    '''static class for forwarding messages to various functions'''
    portees: dict[int, list] = dict()
   
    @staticmethod
    async def port_message(message: discord.Message):
        '''called by bot'''
        if message.guild.id in Port.portees.keys():
            for fn in Port.portees[message.guild.id]:
                if iscoroutinefunction(fn):
                    asyncio.create_task(fn(message))
                else:
                    fn(message)
    @staticmethod
    def add_portee(guild_id, portee):
        if guild_id not in Port.portees.keys():
            Port.portees[guild_id] = []
        Port.portees[guild_id].append(portee)
    
    @staticmethod
    def remove(guild_id):
        del Port.portees[guild_id]
        
        
class QCord(discord.client.Client):
    '''Custom Bot Class'''
    
    def __init__(self, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guild_messages = True
        intents.members = True
        intents.guilds = True
        
        '''Singleton'''
        super().__init__(*args, **kwargs, intents = intents)
        
        self.tree= commands.CommandTree(self)
        self.__exts = dict()
        self.synced = False     # Used to prevent syncing commands more than once.
        
    def __new__(cls):
        '''hairy mess to implement singleton'''
        if not hasattr(cls, 'instance'):
            cls.instance = super(QCord, cls).__new__(cls)
       
        return cls.instance

    
    async def on_message(self, message: discord.Message):
        '''Grabs messages sent and ports them to game instances through Port'''
        if message.author == self.user:
            return
        
        await Port.port_message(message)
        
    async def on_ready(self):
        '''start up regular loops and syncs commandtree'''
        logger.LOGGER.info(f"Succesfully logged in as {self.user}")
        
        import main
        from disc import game
        main.check_queue.start() #ignore error markation
        game.prune_games.start() #^^
        
        await self.tree.sync()
        self.synced = True
        
    async def on_guild_channel_delete(self, channel : TextChannel):
        '''deletes all Reader instance of the channels instances''' 
        from disc import game
        if channel.id in game.SESSIONS.keys():
            game.SESSIONS[channel.id].end(silent=True)
            del game.SESSIONS[channel.id]
            logger.LOGGER.warn("Channel with game instance deleted! Shutting down everything for {}-{}".format(channel.guild.name, channel.name))
            
    async def on_guild_remove(self, guild:Guild):
        '''removes portees for the guild id'''
        if guild.id in Port.portees.keys():
            Port.remove(guild.id)
    
    def load_ext(self, ext: str, *, package = None, sync = False):
        '''Some meta stuff to load modules containing setup function by passing in the bot'''
        ext = util.resolve_name(ext, package)
        
        if ext is not None:
            
            spec = find_spec(ext, package)
            if not spec:
                raise Exception(f"Can't find module: {ext}")
            
            lib = util.module_from_spec(spec)
            sys.modules[ext] = lib
            spec.loader.exec_module(lib)
            
            try:
                setup = getattr(lib, 'setup')
            except AttributeError:
                del sys.modules[ext]
                raise Exception("No setup entry for module: " + ext)
            
            try:
                loop = asyncio.get_running_loop()
                
                loop.create_task(setup(self))
            except (RuntimeError):
                asyncio.run(setup(self))
            
            self.__exts[ext] = lib
            
        else:
            raise Exception("Extension not found")
        
    async def sync(self):
        '''synchronize commandtree'''
        if self.ready:
            try:
                await self.tree.sync()
            except RuntimeError as e:
                print("Well your bot isnt initialized")
                raise e
        
    def load_extensions(self, *args, sync = False):
        '''helper function'''
        for ext in args:
            self.load_ext(ext, sync=sync)
    
    
def init():
    ''' initialises bot and additional dependencies'''
    CLIENT: QCord = QCord()
    
    CLIENT.load_extensions("disc.ext.base_commands", sync = False)
    
    return CLIENT
    