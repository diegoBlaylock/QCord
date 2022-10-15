'''
Created on Oct 1, 2022

@author: diego
'''
import os
import logger
import asyncio
from importlib import reload
from disc.qcord import QCord, init
from discord.ext import tasks
from quiz.utils.PriorityQueue import PQueue

FILE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
_coro_queue = PQueue()

def main():
    init() #QCord.init
    CLIENT().run('NjA4MTA5NzUwNTMzNzUwNzg0.GfN--9.Au63P8gNTcNbZsW0SDNBm-lr61qOlCGvDnNKLA')
    
async def delay(fn, second: float):
    '''Function async decorator that adds a delay to the front of a task'''
    
    async def wrap(*args, **kwargs):
        '''wrapper'''
        await asyncio.sleep(second)
        return await fn(*args, **kwargs)
        
    return wrap


def CLIENT()->QCord:
    '''Return QCORD/BOT singleton instance'''
    return QCord.instance #Ignore error

@tasks.loop(seconds=0.5)
async def check_queue():
    '''This handles a Priority Queue of couroutine tasks
    
    The idea behind this is for other threads to access the main thread, especially because discord.py complains about multithreading
    '''
    
    while _coro_queue:
        asyncio.create_task(_coro_queue.pop_task())
        await asyncio.sleep(0.001)
        
def get_user(user_id):
    '''return user from id
    returns None if none found
    '''
    return CLIENT().get_user(user_id)
        
def submit_coro(coro, priority = 0):
    '''submits task to task queue'''
    _coro_queue.add_task(coro, priority)

if __name__ == '__main__':    
    main() # runs program/ entry point
    
