from adhocracy.tests import *

class TestUserController(TwillTestController):
    
    def test_logging_in_as_admin(self):
        tc.go("http://adhocracy.lan:5000/")
        tc.code("200")
        tc.fv("1", "login", "admin")
        tc.fv("1", "password", "password")
        tc.submit("0")
        tc.code("200")
        tc.find("admin")
        tc.find("settings")
        tc.find("logout")
        
        tc.follow("logout")
        tc.code("200")
        tc.notfind("admin")
        tc.notfind("settings")
        tc.notfind("logout")
        
    
        
        