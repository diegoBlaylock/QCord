'''
Has all the base commands, mostly to create, remove, modify game instance. Can also display scores

@author: diego
'''
from discord import app_commands
from importlib import reload
import discord
from typing import Optional
from quiz.utils.settings import Setting, SettingTransformer
from disc import game
from discord.channel import TextChannel
    
_command_cache: str = None #Used by get_commands. Unnessecary preoptimization ;)
    
@app_commands.command(description = 'Starts a game ')
@app_commands.describe(setting = "Optional: The setting from /settings list to start with. If confused type /settings help")
async def start( interaction: discord.Interaction, setting: Optional[app_commands.Transform[Setting, SettingTransformer]]):
    
    await game.add_game(interaction,setting)
    
@app_commands.command(description="Stops but doesn't kill the running game. To start again, use \".n\"")
async def stop( interaction: discord.Interaction):
    await game.stop_game(interaction)
    
    
@app_commands.command(name = '_kill'
                      , description='Kills current game instance (You have to restart using "/start")')
async def kill( interaction: discord.Interaction):
    await game.kill_game(interaction)
    
@app_commands.command(description="Used to move an active game to another channel")
async def migrate( interaction: discord.Interaction, channel: TextChannel):
    await game.migrate_channel(interaction, channel)
    
@app_commands.command(description="List of Commands")
async def qcord( interaction: discord.Interaction):
    await interaction.response.send_message(get_commands() , ephemeral=True)
    
@app_commands.command(description="Print Scores for current game")
async def score( interaction: discord.Interaction):
    try:
        await interaction.response.send_message(game.get_game(interaction.channel_id).score_str() , ephemeral=True)
    except KeyError:
        await interaction.response.send_message("Sorry! Looks like no game was started here. Use \"start\"" , ephemeral=True)

def get_commands(tree:app_commands.CommandTree = None):
    '''Returns string of commands and their descriptions. Used as a help function'''
    global _command_cache
    if not tree and _command_cache:
        return _command_cache    
    
    str_builder = list()
    str_builder.append(">>> **You found the help section!**")
    
    for command in tree.walk_commands():
        str_builder.append(f"    {command.name.capitalize() : <12}: `{command.description}`")
        
    _command_cache = "\n".join(str_builder)
    return _command_cache

def _tree_helper(bot, *fns):
    '''simple helper to make code more readable'''
    for fn in fns:
        bot.tree.add_command(fn)
        
async def setup(bot):
    '''attaches commands to bot'''
    _tree_helper(bot, start, stop, kill, migrate, qcord, score)
    get_commands(bot.tree)
    
    