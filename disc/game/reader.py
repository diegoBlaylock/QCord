'''
This is the imfamous reader, better known as the GOD CLASS or HEFTY BOY
Contains most functionality pertainent to controls for reading questions
to reading the question to the user.

@attention: DISCORD allows a limit of 5 requests per 5 seconds. Can't do faster than that
        all requests in code are limited to at least once per second
@bug: multiple. Mostly the idea of pausing a multitude of asynchronise tasks lead to 
    tons of checking everywhere and halts. this means usually before every sent message
    checking if the instance is paused, ended, yada yada. basically spaghetti. If you come
    up with a better solution please tell me!
@todo: implement settings and configurations
@author: diego
'''
import discord
import asyncio
import time
import disc
import traceback
import logger

from holer import holers
from disc.game.gamedata import GameData
from enum import Enum, IntFlag
from quiz.utils.settings import Setting
from discord.abc import GuildChannel, Snowflake
from concurrent.futures.thread import ThreadPoolExecutor
from asyncio.tasks import Task
from discord.message import Message
from discord.abc import Messageable
from importlib import reload
from concurrent.futures._base import Future
from disc import game
from collections import deque
from holer.holers import _Holer


async def pause_block(self):
    '''No idea why this exists outside the class, blocks asynchonously if paused'''
    while self.state == _state.PAUSED:
        await asyncio.sleep(0.2)
        

def string_builder(*words):
    '''Fun little generator
    ineffecient but it amuses me
    use send to send in the next letter it 
    should append and next to return the string
    '''
    
    strings=[]
    strings.extend(words)
    while True:
        i=(yield "".join(strings))
        if i is None: 
            yield "".join(strings)
            continue
        strings.append(i)

def wait(func):
    ''' function decorator to add a callback to task
    once the task is done, the callback is called
    '''
    
    def wrap( *args,  callback=None, **kwargs):
        task: Task = asyncio.create_task(func( *args, **kwargs))
        if callback:
            task.add_done_callback(callback)
        
    return wrap


def execute(func):
    ''' function decorator to run something in another thread
    if the original function has a callback keyword, it will run after the task is done'''
    def wrap(self, *args,callback = None, **kwargs):
        future: Future = self.executor.submit(func, self, *args, **kwargs)
        
        if callback:
            future.add_done_callback(callback)
            
        return future
    return wrap


class _state(Enum):
    '''Cute little state enum'''
    RUNNING= 0,
    PAUSED=1,
    IDLE=2
    
    def get(self):
        return self.value
    
class _config(IntFlag):
    '''bitwise flag enum. Planned for game configuration'''
    NULL=0,
    BUZZ_MULITPLE=1,
    SKIP_LOCKED=1<<1

class Reader():
    ''' This class is the representation of a game instance in a channel
    It recieves messages from the port class, thus allowing the user to control the behaviour of this class
    Its basic function is to read a question to the discord user and allow the user to "buzz" and try to answer
    it will change the score of the user and give the answer if no one answered
    
    @note: Asynchronised code is HARD, as said in the top comment, this class provides pause functionality
    by putting blocking/ or ending checks before every sent message
    '''

    #configuration of read rate. Because of discord's rate limiting, 
    #more than one word has to be read at a time: 5 words for a 50 millisecond a character
    S_PER_CHAR = 0.035
    W_PER_REQ = 8
    
    
    def __init__(self, interaction: discord.Interaction, sets: Setting = None):
           
        self.settings = Setting() if not sets else sets
        self.channel_id: int = interaction.channel_id
        self.guild_id: int = interaction.guild_id
        self.holer: _Holer = holers.get_questions(self.settings) 
        self.data: GameData = GameData(interaction)
        self.state: _state = _state.IDLE
        self.buzz_queue = deque()
        self.config = _config.NULL
        disc.qcord.Port.add_portee(self.guild_id, self.get_message)
        if not hasattr(self, "executor"):
            self.executor = ThreadPoolExecutor(10, "reader")
            
    
    async def get_message(self, message: Message):
        '''The portee for the disc.qcord.Port class
        handles a message and checks for commands[
            '.b' - buzz
            '.p' - pause
            '.n' - next Q
            '.r' - resume
            '.s' show scores
        
        If the reader is in buzz state, and the message is authored by the buzzer. 
        His answer is checked. Otherwise all messages are treated as comments
        '''
        
        if message.channel.id == self.channel_id: # Confines messages to those in the channel
            
            command = message.content.lower().strip()[0:2] #potential command token
            
            is_interaction = True # in case of any valid interation, this is used to 
                #indicate whether to update time of last interaction within Gamedata
            
    
            match command:
                case '.b': #buzz case
                    if message.author.id not in self.buzz_queue or _config.BUZZ_MULITPLE in self.config: 
                        '''Has the user buzzed before and is that allowed. If valid:'''
                        await self.pause(timeout=8, buzz=message.author.id)
                        if not self.data.has_user(message.author.id): #If they haven't interacted before, add user to gamedata
                            self.data.add_user(message.author.id)
                    else: # reject buzz
                        bob = await self.get_channel().send("You already buzzed!")
                        await message.delete()
                        await bob.delete(delay=1)
                        
                case '.p': #pause case
                    await self.pause()
                case '.n': #next Q case
                    if (self.is_running() or self.is_paused()) and _config.SKIP_LOCKED in self.config: 
                        #if current game running, is it allowed to skip?
                        pass
                    else:
                        if self.is_running() or self.is_paused():
                            #end game if running
                            self.end()
                            await asyncio.sleep(1)
                        if not self.data.has_user(message.author.id):
                            self.data.add_user(message.author.id)
                        await self.start()
                case '.r': #resume case
                    self.state=_state.RUNNING
                case '.q': #quit
                    self.end()
                    
                case '.s': #score case
                    async def wait_till(self):
                        while not self.is_idle():
                            await asyncio.sleep(0.2)
                            
                        await self.print_scores()
                    
                    import main
                    
                    main.submit_coro(wait_till(self))
                    
                case _: #any other input
                    if self.data.has_user(message.author.id) and self.is_buzzed() and self.buzz_queue[0] == message.author.id:
                        #if buzzed and buzzer author of message
                        await self.check_answer(message)
                    else:
                        is_interaction = False
            if is_interaction:
                self.data.update(message.author.id)
                
                
    def update_settings(self, setting: Setting):
        '''
        @todo implement setting
        '''
        self.hole = holers.get_questions(setting)
        
    
    async def start(self, immediate = True):
        ''' starts functions and creates save'''
        
        self.state = _state.RUNNING
        self.save = Save(self.get_channel(), self.holer.pull(1))
        
        if immediate:
            self.save.init(callback=self.__start)
        else:
            await self.get_channel().send(f'Game is started here, use ".n" to start next question!{self.save.answer}')
    
    @execute
    def __start(self, result):
        
        ### TODO: QUEUE IS GETTING BACKED UP. POSSIBLITITIES: LOOK AT PRIORITY QUEUE TO SCHEDULE IMMEDIATE TASKS AND ALLOW TASKS TO BE DEFFERED OR CANCELED
        ### TRY GROUPING ASYNCIO SLEEP WITH MESSAGE EDITING TO MAKE SURE QUEUE IS NOT OVERLOADED.
        ### LOOK AT THROTTLING FOR BACKLOG
        ### advanced parrellel priority queue event loop mechanishm
        
        try:
            logger.LOGGER.info("New game started - %s %s (%s)", self.get_channel().guild.name, self.get_channel().name, game.SESSIONS[self.channel_id])
            result.result()
            
            import main
            
            async def _edit_task():
                ''' An inner function representing the functionality of 
                continous reading to the discord channel. contains block and checks
                for pausing
                '''
                
                while self.save.has_next(): #while more needs to be read
                    
                    match self.state: 
                        case _state.PAUSED:
                            while self.state == _state.PAUSED:
                                await asyncio.sleep(0.5)
                        case _state.IDLE:
                            return
                    ### PAUSE CHECK
                    
                    text, num = self.save.next()
                    prev = time.time()
                    await self.save.edit(content=f"```  {text}```") # send edited message
                    lag = time.time()-prev    
                   
                    await asyncio.sleep(max((self.S_PER_CHAR  *num)-lag+0.02, 1.02-lag)) # sleep depending on  character count and lag. minimum is 1 second due to rate limiting 
                    
                if self.state is not _state.IDLE:   
                    logger.LOGGER.info(f'{self.save.answer.split("[")[0]}')                
                    match self.state:
                        case _state.PAUSED:
                            while self.state == _state.PAUSED:
                                await asyncio.sleep(0.5)
                        case _state.IDLE:
                            return
                        ### PAUSE CHECK
                        
                        case _: # at the end give 5 seconds for the user to answer
                            await self.countdown(f"```  {self.save.current()}```",5, should_block=True, callback = self.end)
                    
            main.submit_coro(_edit_task())
                 
        except Exception:
            # debugging for thread exceptions
            with open("exceptions.log", "w") as f:
                traceback.print_exc(file=f)
            
                
    async def countdown(self, text:str, time: int, should_block=False, callback = None):
        '''Function that puts a countdown to the end of the reader.
        @param should_block: special paramater. Whether if paused this should block. if false, it will end when running 
        '''
        build = string_builder()
        next(build) #initialize builder
        
        for i in range(time): # Count down and sleep
            if should_block:
                await pause_block(self)
            if self.is_idle() or (self.is_running() and not should_block):
                return
            await self.save.edit(content="{}`[{:{}}]`".format(text, build.send(str(time-i)), time+1))
            await asyncio.sleep(1)
        
        if should_block:
            await pause_block(self)
        if self.is_idle() or (self.is_running() and not should_block):
            return
        await self.save.edit(content="{}`[{}]`".format(text, build.send("0")))
        
        if callback is not None:
            callback()
        
        build.close()

    async def migrate(self, channel_id:int):
        '''Used to migrate channel'''
        import main

        if self.state is _state.RUNNING or self.state is _state.PAUSED: # end if running
            self.end()
        old_channel = self.get_channel()
        next_channel:GuildChannel = main.CLIENT().get_channel(channel_id)
        if not(next_channel and next_channel.type == discord.enums.ChannelType.text):
            await old_channel.send(f"Sorry, I couldn't find channel {next_channel.name}")
        else: 
            self.channel_id = channel_id
            self.guild_id = next_channel.guild.id            
        
    async def pause(self, timeout: int = None, buzz: int=None):
        '''used to generally pause meaning one of two things: natural pause or a buzz
        @param buzz: if none, a natural pause is assumed, otherwise a user id must be supplied
        @param timeout: adds a limit to the pause
        '''
        
        if self.state == _state.RUNNING:
            import main
            
            self.state = _state.PAUSED
            if buzz:
                ''' Some convoluted code. So let me explain to you the heck of the buzz_queue. I truly am sorry
                
                L: So the buzz_queue holds two types of info. at the left end of the queue, user_id are a
                    ppended to signify the users who have buzzed
                R: on the right end a boolean value is appended and popped to signify whether it is in buzz state
                
                So the queue might look light this:
                [user_1=>id, user_2=>id, ..., True]
                '''
                self.buzz_queue.appendleft(buzz)
                self.buzz_queue.append(True)
                main.submit_coro(self.countdown(f"{self.save.message.content}***`[BUZZ: "
                                                f"{self.get_channel().guild.get_member(buzz).display_name}]`***", timeout), priority = -1)
            else:
                
                main.submit_coro(self.save.edit(content = f"```  {self.save.current()}```***`[PAUSED]`***"), priority = -1)
            
            
            if timeout:
                async def task():

                    await asyncio.sleep(timeout+0.1)
                    if self.is_paused():
                        
                        await self.resume()
                main.submit_coro(task())
            
        else:
            logger.LOGGER.warning("Can't pause if game instance is Running or Idle ?")
            
    async def resume(self):
        '''resume state, if buzzed remove buzz state from buzz queue'''
        if self.state == _state.RUNNING:
            logger.LOGGER.warning("Trying to resume a running game Instance")            
        else:
            if self.is_idle():
                logger.LOGGER.warning("Trying to resume an idled game?")
            else:
                if True in self.buzz_queue:
                    self.buzz_queue.pop()
                    if all(x in self.buzz_queue for x in self.data.get_users()) and _config.BUZZ_MULITPLE not in self.config:
                        self.end()
                        return
                self.state = _state.RUNNING
                
    def end(self, silent=False):
        '''terminates current reader execution and prepares for next question'''
        if self.state is _state.PAUSED or self.state is _state.RUNNING:
            self.buzz_queue.clear()
            
            self.state=_state.IDLE
            
            if not silent:
                logger.LOGGER.info("Game Ended - %s %s (%s)", self.get_channel().guild.name, self.get_channel().name, game.SESSIONS[self.channel_id])
                self.print_answer()
               
    def print_answer(self):
        '''this is what will be displayed in the end'''
        import main
        main.submit_coro(self.save.edit(content=f"```  {self.save.current()}```***`[FINISHED]`***\n\n`ANSWER: {self.save.answer}`"))
        
    async def print_scores(self):
        builder = string_builder()
        next(builder)
        
        import main
        builder.send("*SCORES:*    ")
        for u, stamp in self.get_scores().items():
            builder.send(f"{self.get_channel().guild.get_member(u).display_name}: `{stamp[0]}`\t")
        
        string = builder.send(None)
        await self.get_channel().send(content=builder.send(string))
        
                 
    def score_str(self):
        '''returns the scores as a string, same functionality as print_scores except for printing
        feel free to change it, I made it two ways for fun
        '''
        import main
        return "*SCORES*:    " + "\t".join([f"{main.get_user(u).display_name}: `{stamp[0]}`" for u, stamp in self.get_scores().items()])
        
    def get_channel(self)-> Messageable:
        '''get channel from self.channel_id'''
        import main

        channel = main.CLIENT().get_channel(self.channel_id) 
        
        if not channel:
            raise Exception("Channel not found")
        return channel
    
    async def check_answer(self, message: Message):
        '''Checks answers and responds to the correctness
        
        stopping ands incrementing score for right answer,
        or resuming and penalty for wrong
        @todo: Make the string matching more merciful with fuzzy comparisons
        '''
        
        answer = self.save.answer.split("[")[0].split("(")[0] #Another problem is the answer text can have comments such as [prompt on... (accept this...
        
        if message.content.strip().lower() == answer.strip().lower():
            await self.get_channel().send(content="*`[CORRECT]`*", reference = message, mention_author=True)
            self.data.increment(message.author.id, 10)
            self.end()
        else:
            await self.get_channel().send(content="*`[INCORRECT]`*", reference = message, mention_author=True)
            self.data.increment(message.author.id, -5)
            await self.resume()
            
    def get_users(self)-> list[Snowflake]:
        return self.data.points.keys()
    
    def get_scores(self):
        return self.data.points.copy()
    
    def is_running(self)->bool:
        return self.state is _state.RUNNING
    
    def is_idle(self)->bool:
        return self.state is _state.IDLE
    
    def is_paused(self) -> bool:
        return self.state is _state.PAUSED
    
    def is_buzzed(self) -> bool:
        return True in self.buzz_queue
    
class Save():
    ''' This is here to allow for pausablity
    Hold the data for the question,
    which word we are on while reading,
    the message object that needs to be edited
    '''
    def __init__(self, ch, question: dict[str, str]):
        self.index = 0
        self.question: str = question['q']
        self.answer: str = question['a']
        self.category: str = question['s']
        self.message = None
        self.channel = ch
        self.array: tuple[str] = self.question.split(" ")
        
    def has_next(self) -> bool:
        return self.index < len(self.array)
    
    def next(self):
        length = len(self.array[self.index])
        self.index +=1
        
        
        for _ in range(1, Reader.W_PER_REQ):
            if self.has_next():
                length+=len(self.array[self.index])
                self.index+=1
            else:
                break
        
        
        return " ".join(self.array[:self.index]), length
    
    def current(self):
        return " ".join(self.array[:self.index])
    @wait
    async def init(self):
        if self.message is None:
            self.message = await (self.channel.send("loading..."))
        return self.message
    
    async def edit(self, content=None):
        self.message = await self.message.edit(content=content)