import threading

__author__ = 'Serebatos'
import SocketServer
import os
import pickle
import sched
import time
import datetime
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_h.settings")
from h_ctrl.models import Action, ActionSchedules, Schedule, Pi, Home


class Core(object):
    statDict = dict()
    ON = 1
    OFF = 0

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Core, cls).__new__(cls)
        return cls.instance


    def set_on(self, key):
        self.set_val(key, Core.ON)

    def set_off(self, key):
        self.set_val(key, Core.OFF)

    def invert(self, key):
        if key in self.statDict and self.statDict[key] == 0:
            self.set_on(key)
            print "Turning On"
        else:
            self.set_off(key)
            print "Turning Off"

    def set_val(self, key, val):
        self.statDict[key] = val

    def get_status(self):
        return self.statDict

    def get_or_add_action(self, action):
        if action in self.statDict:
            return {action: self.statDict[action]}
        else:
            self.statDict[action] = 0
            return {action: self.statDict[action]}


class MyTCPHandler(SocketServer.BaseRequestHandler):
    c = Core()
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def __init__(self, request, client_address, server):
        print "On Enter current status={}".format(c.get_status())
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)


    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        d = pickle.loads(self.data)
        print "id=" + d["id"]
        print "type=" + d["type"]
        print repr(d)
        print Action.objects.get(pk=d["id"])
        # action = c.get_or_add_action(self.data)
        # c.invert(self.data)
        # print "On Exit current status={}".format(c.get_status())
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


class Backend(object):
    c = 0
    schedDict = dict()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Backend, cls).__new__(cls)
        return cls.instance

    def exec_action(self, actionschedules, prev_actionschedules):
        if actionschedules.skip == False:
            print "%s" % time.time(), "Running action:%s" % actionschedules.action.name
        else:
            print unicode("Skipping action:{}".format(actionschedules.action.name))

    def exec_schedule(self, schedule):
        scheduler = sched.scheduler(time.time, time.sleep)
        db_schedule = Schedule.objects.get(pk=schedule.id)
        prev_act_sch = None
        count = 0
        act_list=list()
        for act_sched in db_schedule.actionschedules_set.all():
            print "Action '%s' is queued." % act_sched.action.name, " Start time is %s" % act_sched.start_time
            # newTime = timezone.localtime(act_sched.start_time)
            dt = datetime.datetime.now()
            # time_float = (act_sched.start_time - newTime.utcfromtimestamp(14400)).total_seconds()
            # print "real: %s" % act_sched.start_time.

            tt=  time.mktime((dt.year,dt.month,dt.day,act_sched.start_time.hour,act_sched.start_time.minute,act_sched.start_time.second,dt.weekday(),dt.timetuple().tm_yday,-1))
            print "time: %s" % tt
            action_sched= scheduler.enterabs(tt, 1, self.exec_action, (act_sched, prev_act_sch))
            act_list.append(act_sched)
            prev_act_sch = act_sched
            count += 1
        if count >0:
            self.schedDict[act_sched.schedule.id]={"scheduler":scheduler,"actions":act_list}
        print "Schedule '%s' is planned." % db_schedule.name, "Total actions %s" % str(count)
        print("...")
        print("...")
        # scheduler.run()
        # Start a thread to run the events
        t = threading.Thread(target=scheduler.run)
        t.start()
        # threading.Timer()
        print("exit")


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    c = Core()
    print "n={}".format(c.get_status())
    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    # server.serve_forever()
    b = Backend()
    s = Schedule.objects.get(pk=1)
    print "b={}".format(str(b.c))
    b.exec_schedule(s)
    # print "Now: %s" % time.time(), "Datetime:%s" % s.last_run
    #
    # newTime = timezone.localtime(s.last_run)
    # strTime = str(newTime).replace("+04:00", "")
    # print(strTime)
    # newTime2 = time.strptime(strTime, '%Y-%m-%d %H:%M:%S.%f')
    #
    # dt = datetime.datetime.now()
    # print "time now: %s" % time.time()
    # print "from timestamp: %s" % datetime.datetime.fromtimestamp(1408368379.85)
    # print "dt: %s" % dt
    # print "total: %s" % (dt - dt.utcfromtimestamp(14400)).total_seconds()
    # dt = datetime.datetime.fromtimestamp(1408369448.38)
    # # dt = timezone.localtime(dt)
    # print "from timestamp2: %s" % dt
    # print "day: %s" % datetime.datetime.fromtimestamp(time.time())

    # print "Now: %s" % datetime.datetime.now(), "Datetime:%s" % newTime, "Now > Datetime = %s" % (datetime.datetime.now() > timezone.localtime(s.last_run))

    # class MyTCPHandler(SocketServer.StreamRequestHandler):
    #     count = 0
    #
    #     def __init__(self, request, client_address, server):
    #         MyTCPHandler.count = MyTCPHandler.count+1
    #         print "n={}".format(MyTCPHandler.count)
    #         SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
    #
    #
    #     def handle(self):
    #         # self.rfile is a file-like object created by the handler;
    #         # we can now use e.g. readline() instead of raw recv() calls
    #
    #         self.data = self.rfile.readline().strip()
    #         print "{} wrote!:".format(self.client_address[0])
    #         print self.data
    #         # Likewise, self.wfile is a file-like object used to write back
    #         # to the client
    #         self.wfile.write(self.data.upper())