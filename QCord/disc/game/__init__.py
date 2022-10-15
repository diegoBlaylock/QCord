''' Somewhat the facade for the game instances (Readers)
keeps track of various readers and of getting rid of long
in active instances
'''

import discord
import asyncio
import time
from disc.game.reader import Reader
from orjson import loads
from main import FILE_ROOT as base
from discord import ui
from discord.ext import tasks
from discord.channel import TextChannel
from disc import qcord
from idlelib.sidebar import BaseSideBar

SESSIONS:dict[int, Reader] = dict()
CONTROLS: tuple[tuple, dict[str, str]] #TODO: implement

with open(f"{base}/disc/game/controls.json") as file: ### Read in controls file
    CONTROLS = loads(file.read())


async def add_game(interaction: discord.Interaction, setting):
    '''Add a game instance'''
    if interaction.channel_id in SESSIONS.keys(): #Check if game instance exists
        await interaction.response.send_message('Game already started!'
                                                '\nSend ".n" to begin next question!' )
    else:
        await interaction.response.send_message(f'Game Started: use "/score" to see '
                                                'your scores')

        SESSIONS[interaction.channel_id] = Reader(interaction, setting)
        import main
        main.submit_coro(SESSIONS[interaction.channel_id].start(),-1)

async def stop_game(interaction: discord.Interaction):
    '''stops a game instance but doesn't kill it. Scores are still loaded'''
    
    if interaction.channel_id in SESSIONS.keys(): #Check if game instance exists
        
        SESSIONS[interaction.channel_id].end()        
        await asyncio.sleep(1)
        await interaction.response.send_message('Stopped game, use ".n" to start next question!', ephemeral = True )
        
    else:
        await interaction.response.send_message(f'No Game Started! Use "/start" to start game!', ephemeral = True)
        
async def kill_game(interaction: discord.Interaction):
    '''kills and deletes and instance'''
    
    if interaction.channel_id in SESSIONS.keys(): #Check if game instance exists
        SESSIONS[interaction.channel_id].end(silent=True)
        
        await interaction.response.send_message('Killed game, here are the final scores:')
        await SESSIONS[interaction.channel_id].print_scores()
        del SESSIONS[interaction.channel_id]
    
    else:
        await interaction.response.send_message(f'No Game Started! Use "/start" to start game!',\
                                                ephemeral = True)
     
async def migrate_channel(interaction: discord.Interaction, channel: TextChannel):
    '''Used to change the channel of an instance'''
    
    if interaction.channel_id in SESSIONS.keys(): #Check if game instance exists
        if channel.id in SESSIONS.keys():
            await interaction.response.send_message(f'Game already started in #{channel.name}!\nSend ".n" to '
                                                    'begin next question!' )
            return
        read:Reader = SESSIONS[interaction.channel_id]
        read.end()
        await read.migrate(channel.id)
        SESSIONS[channel.id] = read
        del SESSIONS[interaction.channel_id]
        await interaction.response.send_message(f"Moving game to #{channel.name}")
        await SESSIONS[channel.id].start(immediate = False, )
        
    else:        
        if channel.id in SESSIONS.keys():
            await interaction.response.send_message(f'Game already started in #{channel.name}!\nSend ".n" '
                                                    'to begin next question!' )
        else:
            await interaction.response.send_message(f'There was no game started here, started a game in #{channel.name}')
    
            SESSIONS[channel.id] = Reader(interaction, None)            
            await SESSIONS[channel.id].start(immediate = False)
            
            
def del_game(channel_id):
    import main    
    SESSIONS[channel_id].end(silent=True)
    del SESSIONS[channel_id]
    

def games_in_guild(guild):    
    '''TODO: get all game instances for a guild
    '''
    pass


def get_game(channel_id):
    return SESSIONS[channel_id]

@tasks.loop(hours=2)
async def prune_games():
    '''checks every 2 hours for long inanactive reader (6hours) and cleans them
    think of a garbage collector
    '''
    
    current_time = time.time()

    for read in SESSIONS.copy().values(): # cycles through readers
        since_last_interaction = current_time - read.data.last_interaction
        
        if since_last_interaction > 21600:
            del_game(read.channel_id)
        else:
            for u, t in read.data.points.copy().items(): # Cycles though Users
                
                if current_time - t[1] > 21600:
                    read.data.del_user(u)