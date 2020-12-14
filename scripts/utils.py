import threading
import time
from . import views
import numpy as np
import pandas as pd
from django.http import HttpResponse

class ThreadingExample(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=1):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval
        # self.thread
        thread = threading.Thread(target=views.Results, args=())
        thread.daemon = True                           
        thread.start()
                                     
    def thread(self,request):               
        html = "<html><body>It is now yayy time and the function is successfully deployed!!</body></html>"
        return HttpResponse(html)

    def run(self):
        """ Method that runs forever """
        while True:
            # Do something
            print('Doing something imporant in the background')

            time.sleep(self.interval)
    

# example = ThreadingExample()
# time.sleep(3)
# print('Checkpoint')
# time.sleep(2)
# print('Bye')