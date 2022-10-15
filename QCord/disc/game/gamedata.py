'''
Created on Oct 3, 2022

@author: diego
'''
import discord
from typing import Union
import time

class GameData():
    '''Simply holds data. Organized in a dictionary[user_id: [points, time of last interaction]]'''
    
    def __init__(self, interaction: discord.Interaction):
        self.points: dict[int, list[int, int]] = dict()
        self.add_user(interaction.user.id)
        self.last_interaction = time.time()
        
    def update(self, user_id: int):
        '''update users time-wise'''
        t = time.time()
        self.points[user_id][1] = t
        self.last_interaction = t
        
    def increment(self, user_id: int, by: int):
        '''edit users points and subsequently time'''
        self.update(user_id)
        self.points[user_id][0]+= by
        
    def add_user(self, user_id, *, point=0):
        self.points[user_id] = [point, 0]
        
    def del_user(self, user_id):
        del self.points[user_id]
        
    def get_score(self, user_id):
        return self.points[user_id][0]
    
    def get_users(self):
        return self.points.keys()
    
    def has_user(self, user_id):
        return user_id in self.points.keys()
    
    def __iter__(self):
        '''Wrapper for points iterator, yielding only user_id and score| skipping the time'''
        for k,v in self.points:
            yield k, v[0]