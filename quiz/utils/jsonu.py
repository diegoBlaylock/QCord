'''Loads and Dumps Json Strings
ineffectient but a cool side project to have done

Created on Sep 26, 2022

@author: diego
'''

from enum import Enum
from collections import deque
from _collections_abc import Iterable
import string


class TType(Enum):
    NULL=0
    COMMA=1
    COLON=2
    QOUTE=3
    OBJECT_START=4
    OBJECT_END=5
    ARRAY_START=6
    ARRAY_END=7
    STRING=8
    NUMBER=9
    BOOL=10
    END=11


def load(json_string):
    
    tokens = __tokenise(json_string)
    lex = TokenStream(tokens)
    
    return_value = None
    struct_list = deque()
    
    if len(tokens) == 2:
        return tokens[0][1] if len(tokens[0]) == 2 else None
    
    while(lex.has_next()):
        token = lex.next()
        match token[0]:
            case TType.OBJECT_START: #creates dict and adds to stack
                struct_list.append({})
                
            case TType.OBJECT_END: # peeks to see if stack has a dict as last element. Then inserts into previous data structure
                if not struct_list or not isinstance(struct_list[-1], dict):
                    raise InvalidJSONError("Somethings wrong with the JSON Object")
                
                if len(struct_list) > 1:
                    __insert_data(struct_list.pop(), struct_list)                    
                else:
                    struct_list.pop()
                    
            case TType.ARRAY_START:
                struct_list.append([])
                
            case TType.ARRAY_END:
                if not struct_list or not isinstance(struct_list[-1], list):
                    raise InvalidJSONError("Somethings wrong with the JSON Array")

                if len(struct_list) > 1:
                    __insert_data(struct_list.pop(), struct_list)
                else:
                    struct_list.pop()
                    
            case TType.COMMA:
                pass
            case TType.COLON:
                pass
            case TType.STRING:
                if not struct_list:
                    raise InvalidJSONError("there's a floating string in your JSON")
                elif lex.peek()[0] is TType.COLON:
                    if not isinstance(struct_list[-1],dict):
                        raise InvalidJSONError("Can't put key-value pairs here")
                    struct_list.append(token[1])
                else:
                    __insert_data(token[1], struct_list)
                    
            case TType.NUMBER | TType.BOOL:
                if not struct_list:
                    raise InvalidJSONError("there's a floating value in your JSON")
                else:
                    __insert_data(token[1], struct_list)
                    
            case TType.NULL:
                if not struct_list:
                    raise InvalidJSONError("there's a floating value in your JSON")
                else:
                    __insert_data(None, struct_list)
        if return_value is None:
            return_value = struct_list[0]
    return return_value

def __insert_data(obj, struct_list):
    """This inserts the data based on whether into a dict or array"""
    if isinstance(struct_list[-1], str):
        key = struct_list.pop()
        if isinstance(struct_list[-1], dict):
            struct_list[-1][key]=obj
        else:
            raise InvalidJSONError("You can't define keys-value pair here!")
    else:
        struct_list[-1].append(obj)
class TokenStream():
    
    index = 0;
    
    def __init__(self, tokens):
        self.tokens = tokens
        
    def has_next(self):    
        return self.peek() is not TType.END 
    
    def peek(self):
        return self.tokens[self.index]
    
    def next(self):
        self.index+=1
        return self.tokens[self.index-1]
    def next_string(self):
        pass
    
    def next_array(self):
        pass
    def next_dict(self):
        pass
    
class CharStream():
    
    
    
    def __init__(self, input__):
        self.input_ = input__
        self.index = 0
    
    def has_next(self):    
        return self.index < len(self.input_) 
    
    def peek(self):
        return self.input_[self.index]
    
    def next(self):
        self.index+=1
        return self.input_[self.index-1]
    def foward(self, amount=1):
        self.index+=1
        
    
def __tokenise(inp):
    """handle all my problems - returns an array of tokens"""
    stream = CharStream(inp)
    grouper_list = deque()    
    token_list = deque()
    __cycle_whitespace(stream)
     
    while stream.has_next():
       
        match stream.peek():
            case '"': # tokenize a string literal
                token_list.append((TType.STRING, __read_string(stream)))
                
            case ':':
                if token_list[-1][0] is not TType.STRING:
                    raise InvalidJSONError("Can only have strings as keys")
                token_list.append((TType.COLON,))
                stream.foward()
            case ',':
                token_list.append((TType.COMMA,))
                stream.foward()
            case '{':
                token_list.append((TType.OBJECT_START,))
                grouper_list.append(TType.OBJECT_START)
                stream.foward()
            case '}':
                token_list.append((TType.OBJECT_END,))
                if grouper_list and grouper_list[-1] is TType.OBJECT_START:
                    grouper_list.pop()
                else:
                    raise InvalidJSONError("Hanging RBrace")
                stream.foward()
            case '[':
                token_list.append((TType.ARRAY_START,))
                grouper_list.append(TType.ARRAY_START)
                stream.foward()
            case ']':
                token_list.append((TType.ARRAY_END,))
                
                if grouper_list and grouper_list[-1] is TType.ARRAY_START:
                    grouper_list.pop()
                else:
                    raise InvalidJSONError("Hanging RBracket")
                stream.foward()
                
            case _:
                if(__is_numeric(stream.peek())):
                    token_list.append((TType.NUMBER, __read_number(stream)))
                elif __is_bool(stream.peek()):
                    token_list.append((TType.BOOL, __read_boolean(stream)))
                elif stream.peek()=='n':
                    token_list.append((__read_null(stream),))
                else:
                    raise InvalidJSONError()
        __cycle_whitespace(stream)  
        
    if grouper_list: 
        raise InvalidJSONError("Bracketing/quoting not closed")
    token_list.append(TType.END)
    return token_list

def __cycle_whitespace(stream):
    """Skips over whitespace characters in stream
    
    if not in quotes
    """    
    while (stream.has_next() and __is_whitespace(stream.peek())): 
        stream.next()
        
        
def __is_whitespace(char):
    return ord(char) in {0x9, 0xa, 0xb, 0xc, 0xd, 0x85, 0x20}

def __is_control(char):
    return ord(char) <= 0x1f or ord(char) == 0x7f or (0x80 <= ord(char) <= 0x9f)

def __is_numeric(char):
    """Tells if character could possibly be numeric"""
    return char in {'-', '+','0','1','2','3','4','5','6','7','8','9','.','E','e'}
def __read_number(stream):
    if __is_numeric(stream.peek()):
        char_array = deque()
        is_floating = False
        while __is_numeric(stream.peek()):
            if stream.peek() in {'.', 'E', 'e'}:
                is_floating = True
            char_array.append(stream.next())
        return float("".join(char_array)) if is_floating else int("".join(char_array))
    else:
        raise InvalidJSONError(f"couldn't parse: '{stream.peek()}' (u{ord(stream.peek())})")

def __is_bool(char):
    return char in {'f','t'}

def __read_boolean(stream):
    valid = ('true', 'false')
    index_i = 0
    index_j = 0
    
    match stream.peek():
        case 't':
            pass
        case 'f':
            index_i = 1
        case _:
            raise InvalidJSONError("ummm what")
    
    while stream.peek()==valid[index_i][index_j] and index_j != len(valid[index_i])-1:
        if index_j != len(valid[index_i])-1:
            index_j+=1
        stream.foward()
    if index_j != len(valid[index_i])-1:
        raise InvalidJSONError("Couldn't read boolean")
    stream.foward()
    return index_i == 0

def __read_null(stream):
    valid = 'null'
    index_j = 0
    
    while index_j != 3 and stream.peek()==valid[index_j]:
        index_j+=1
        stream.foward()
    if not index_j==3:
        raise InvalidJSONError("Couldn't read boolean")
    stream.foward()
    return TType.NULL
    
def __read_string(stream):
    '''reads a string surrounded by quotes from character stream'''
    stream.foward()
    hit_end = False
    char_array = deque()
    while not hit_end:
        char = stream.next()
        
        match char:
            
            case '"':
                hit_end = True
            case '\\': # handle escaped characters
                match stream.next:
                    case '"':
                        char_array.append('"')
                    case '\\':
                        char_array.append('\\')
                    case '/':
                        char_array.append('/')
                    case 'b':
                        char_array.append('\b')
                    case 'f':
                        char_array.append('\f')
                    case 'n':
                        char_array.append('\n')
                    case 'r':
                        char_array.append('\r')
                    case 't':
                        char_array.append('\t')
                    case 'u':
                        code = "0000"
                        for i in range(4):
                            code[i] = stream.next
                        char_array.append(chr(int(code,16)))
            case _:
                char_array.append(char)
                
    return "".join(char_array)


class InvalidJSONError(Exception):
    """Raised with various Formating Errors"""
    pass



