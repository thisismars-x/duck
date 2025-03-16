
# -----------------------------------------
# Godsend is a quick backend framework that makes making websites more pleasant and convenient.
# It has everything you would need to make robust websites, up and running in the least time 
# possible. Coming under 1200 lines of code, it is designed to be read through by mere mortals and
# used with care. Also, Godsend supports natively running your web application 
# with Gunicorn. Coming support for many more other web servers. Check it out:
# [Godsend](https://github.com/thisismars-x/godsend), and make it better.


# 
# This is your Router Class 
# Use it to make Routes to your application.
# 
# Usage:
# `code
# route = Router('/', index, 'GET', alias='index')
# if route.does_not_exist():
#   raise routeerror("This is the fault of God!")
# `
# 
class Router:

    # Initialize a Router object with URL, function(view function), method(defaults to GET) and alias(not needed)
    def __init__(self, url, fn, method, alias):
        pass 

    def this_is_not_documented(self, x, y):
        pass 

    # When websites are not available, you might need a page to display error 
    # this is the 404 error page 
    ERROR404 = 'base.html'


# 
# This function is the main function of your program which runs your application instance.
# Note that you may not call this function, with port number 22 as it is reserved for ssh.
# `error 
# // this generates error 
# app = run(APP, port=22) 
# 
# // this is fine 
# app = run(APP, port=5050)
#`
def run(app: application, port = 8080):
    pass


# 
# This variable is unset when the program needs to en 
__RUN__COND = True 
