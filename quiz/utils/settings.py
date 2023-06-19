'''
Settings file. Holds categories and subcategories and planned difficulty of questions to display
@author: diego
'''
from enum import Enum
import json
import os
from holer import SETTINGS_JSON
from discord.app_commands.transformers import Transformer
import discord



### init ###

dir = os.path.dirname(__file__)

per_page = 100
__config = json.loads(open(os.path.join(dir, "settings.json")).read())


Category = Enum('Category', __config["Category"])
Sub_Cat = Enum('Sub_Cat', __config["Sub_Cat"])
Difficulty = Enum('Difficulty', __config["Difficulty"])

_tournament_post_template={'q[difficulty_in][]':None, 'commit':'Filter', 'order':'id_asc', 'per_page':400}
######

class Setting():
    

    
    _cat_list = set()
    
    _sub_cat_list = set()
    
    
    
    diff = Difficulty.ANY
    
    
    
    def __init__(self):
        pass
    
    def __str__(self):
        pass
    
    def add_cat(self, cat):
        if self._sub_cat_list:
            for sub in self._sub_cat_list:
                if (sub.name+".dat") in SETTINGS_JSON["Category"][cat.name]:
                    self._sub_cat_list.remove(sub)
        self._cat_list.add(cat)
        
    def add_sub(self, sub):
        
        for cat in self._cat_list:
            
            if sub.name.startswith(cat.name):
                self._cat_list.remove(cat)
                break
        self._sub_cat_list.add(sub)
        
    def rem_cat(self, sub):
        self._cat_list.remove(sub)
    def rem_sub_cat(self, sub):
        self._sub_cat_list.remove(sub)
        
        
    def generate_tossup_params(self):
        '''this is meant for the online version
        
        generates question query
        '''
        payload = _tournament_post_template.copy()
        payload['q[difficulty_in][]'] = self.diff.value
        return payload
    
    def generate_tournament_payload(self):
        '''this is meant for the online version
        
        If you do implement it, difficulty on quizdb references not questions but rather tournaments
        and tournaments have questions. This generates tournaments from which at random questions can 
        be pulled to acheive difficuly parameters
        '''
        payload = _tournament_post_template.copy()
        payload['q[difficulty_in][]'] = self.diff.value
        return payload
    
    
class SettingTransformer(Transformer):
    ''' Still needs to implemented. This is meant for a system where you can name custom settings you like
    and choose from them on the slash commands. This is used by discord.py for their app_commands package'''
    async def transform(self, interaction: discord.Interaction, value: str) -> Setting:
        return Setting()
        