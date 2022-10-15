'''
This module is the interface that allows the readers and game instances to pull questions
from the json files.

This is real simplistic for the json files, but a more advanced interface is needed
for the planned functionality of pulling questions from online quizdb. 
(this feature would allow for a bigger database and selection of questions by difficulty)

@author: diego
'''

from collections import deque
import os
from orjson.orjson import loads
from quiz.utils.settings import Setting
from random import randint
from _collections_abc import Iterable
from holer import SETTINGS_JSON
from main import FILE_ROOT as root




        
def get_qpaths(setting):
    '''will return the file paths for questions from the constraints specified in the setting object
    
    How the jsons are organised is that each subcategory has a file(<category>_<subcategory>.dat) along with
    a <category>_NONE.dat file containing all questions from that category and finally a NONE.dat containing all questions
    '''
    if not(setting._cat_list or setting._sub_cat_list):
        return SETTINGS_JSON["Category"]["NONE"]
    
    elif not setting._sub_cat_list:
        rtn = deque()
        for cat in setting._cat_list:
            rtn.append(f"{cat.name}_NONE.dat")
            
        return rtn
    else:
        rtn = deque()
        for cat in setting._cat_list:
            rtn.append(f"{cat.name}_NONE.dat")
        for sub in setting._sub_cat_list:
            rtn.append(f"{sub.name}.dat")
            
        return rtn
    
def get_questions(setting: Setting):
    return _Holer(get_qpaths(setting))
    
class _Holer(Iterable):    
    '''Iterator with a randimized queue of questions to pull from.
    Ideally every instance is based of a setting object
    '''
    
    def __init__(self, paths):
        self.questions = list()
        
        for path in paths:
            with (open(f"{root}/questions/{path}", "r", encoding="utf8")) as j:
                self.__rinsert(loads(j.read()))
        self.questions = deque(self.questions)    
    
    def __iter__(self):
        while self.questions:
            yield self.questions.popleft()    
        
    def __rinsert(self, itemlist):
        for item in itemlist:
            self.questions.insert(randint(0, len(self.questions)), item)
    
    def pull(self, n=1):
        if n < 1:
            return []
        elif n == 1:
            return self.questions.popleft()
        else:
            rtn = deque()
            for _ in range(n):
                rtn.append(self.questions.popleft())
            return rtn