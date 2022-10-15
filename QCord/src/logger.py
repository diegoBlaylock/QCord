'''
Created on Oct 7, 2022

@author: diego
'''
import logging
import sys

LOGGER = logging.RootLogger(logging.NOTSET)

def init():
    '''sets up 2 handlers/outputs: the console and the qcord.log file
    the file is more verbose''' 
    form = logging.Formatter("[%(asctime)s] [%(levelname)-8s] [%(threadName)s - %(module)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    
    ch=logging.StreamHandler(stream = sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(form)
    
    file = logging.FileHandler("qcord.log", mode='w')
    file.setLevel(logging.NOTSET)
    file.setFormatter(form)
    
    LOGGER.addHandler(ch)
    LOGGER.addHandler(file)
    
def log(message, name=None):
    empty = ""
    LOGGER.info(f"{empty if not name else name}:    {message}")
    
    
init()