'''
This is for the planned version where questions are pulled from an online data base rather than a local one
@author: diego
'''
from requests import Session 
from bs4 import BeautifulSoup as BSoup


class Quiz():
    
    _LOGIN_DATA_TEMPLATE = {'utf8':"%E2%9C%93","authenticity_token":"", "admin_user[email]":"", "admin_user[password]":"", "admin_user[remember_me]":0, "commit":"Login"}
    base_url = "http://www.quizdb.org/admin"
    
    def __init__(self):
        self.session = Session()        
        self.token = ""
        self.logged_in=False    
    
    def __pull_auth_token(self, page):
        soup = BSoup(page, 'lxml')
        return soup.find("meta", {'name':"csrf-token"})['content']
    
    def __get(self, rel_url,*, params = None, data=None, html=False, login=False):
        if not(login or self.logged_in):
            raise NotLoggedIn("You can't access the admin page without logging in")
        
        if data is not None:
            data['authenticity_token'] = self.token
        else:
            data = {'authenticity_token':self.token}
        r = self.session.get(("" if rel_url.startswith('/') else "/").join((self.base_url, rel_url)), params=params, data = data)
        if(html):
            self.token = self.__pull_auth_token(r.text)
        return r
    
    def __post(self, rel_url,*, params = None, data=None, html=False, login = False):
        if not(login or self.logged_in):
            raise NotLoggedIn("You can't access the admin page without logging in")
        
        if data is not None:
            data['authenticity_token'] = self.token
        else:
            data = {'authenticity_token':self.token}
            
        r = self.session.post(("" if rel_url.startswith('/') else "/").join((self.base_url, rel_url)), params=params, data = data)
        if(html):
            self.token = self.__pull_auth_token(r.text)
        return r
        
    def log_in(self, *, email, password):
        self.session.headers["User-Agent"]='QuizCord/1.0.0'
        
        self.__get("login", html=True, login = True)
        
        dat = self._LOGIN_DATA_TEMPLATE.copy()
        dat["admin_user[email]"] = email
        dat["admin_user[password]"] = password
        
        r = self.__post("login", data = dat, html = True, login = True)
        #r = session.post("http://www.quizdb.org/admin/login", data = {'utf8':"%E2%9C%93","authenticity_token":token, "admin_user[email]":email, "admin_user[password]":password, "admin_user[remember_me]":0, "commit":"Login"})
        
        if not r.history:
            raise InvalidCredentials(f"The credentials/email for {email} didn't work")
        self.logged_in = True
        
    
    def get_tournaments(self, setting):
        r = self.__get("tournaments.json", params=setting.generate_tournament_payload())
        return r.json()
    
    def _get_total(self, setting):
        params = setting.generate_tossup_params()
q = Quiz()
q.log_in(email="dbob.ff@gmail.com", password="yoyoyo123")

class NotLoggedIn(Exception):
    pass

class InvalidCredentials(Exception):
    pass
