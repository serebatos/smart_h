# coding=utf-8
import threading

ACT_WAITING = 'W'

ACT_STOPPED = 'S'

ACT_RUNNING = 'R'

__author__ = 'Serebatos'
import SocketServer
import os
import pickle
import sched
import time
import datetime
from subprocess import call
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




    def exec_event(self, actionschedules, prev_actionschedules):
        if actionschedules.skip == False and actionschedules.schedule.enabled == True:
            print "%s" % time.time(), "Running action:%s" % actionschedules.action.name
            self.exec_action(actionschedules.action)

            actionschedules.status = ACT_RUNNING
            actionschedules.save()
            print("Backend. Status saved")

            if prev_actionschedules != None:
                prev_actionschedules.status = ACT_STOPPED
                prev_actionschedules.save()
        else:
            print unicode("Skipping action:{}".format(actionschedules.action.name))
            #todo: как сделать,чтобы после перезапуска распбери все работало и как сделать повторение на след день,
            # как вариант последний шаг заново инициализирует на следующий день шедулер
        db_schedule = Schedule.objects.get(pk=actionschedules.schedule.id)
        db_schedule.last_run = datetime.datetime.now()
        db_schedule.save()



    def exec_action(self, action):
        actObj = Action.objects.get(pk=action.id)
        # command = ["python", "/home/pi/dev/scripts/switch.py", "%s" % actObj.pin, "%s" % actObj.cmd_code]
        # res = call(command)



    def exec_schedule(self, schedule):
        db_schedule = Schedule.objects.get(pk=schedule.id)
        if db_schedule.enabled == True:
            prev_act_sch = None  #previous action which status should be changed to "Completed'
            count = 0
            act_list = list()
            self.scheduler = sched.scheduler(time.time, time.sleep)
            self.evt_list = act_list
            dt = datetime.datetime.now()

            for act_sched in db_schedule.actionschedules_set.all():
                print "Action '%s' is being putted in queue." % act_sched.action.name, "Start time is %s" % act_sched.start_time

                # time_float = (act_sched.start_time - newTime.utcfromtimestamp(14400)).total_seconds()
                tcur = time.time()
                tt = time.mktime((dt.year, dt.month, dt.day, act_sched.start_time.hour, act_sched.start_time.minute,
                                  act_sched.start_time.second, dt.weekday(), dt.timetuple().tm_yday, -1))
                #todo: add planned start time to act_sched
                if tcur > tt:
                    dt = dt.combine(dt.date(), act_sched.start_time)
                    dtstart = dt + datetime.timedelta(days=1)
                    tt = time.mktime((dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute,
                                      dtstart.second, dtstart.weekday(), dtstart.timetuple().tm_yday, -1))
                    print "Backend. Start time is in the past. Planning this action(%s)" % act_sched.action.name, "on %s" % dtstart
                # planned event
                event_sched = self.scheduler.enterabs(tt, 1, self.exec_event, (act_sched, prev_act_sch))

                # Статус в "Ожидание" выполнения
                act_sched.status= ACT_WAITING
                act_sched.save()

                # collected to list
                self.evt_list.append(event_sched)
                prev_act_sch = act_sched
                count += 1
            if count > 0:
                self.schedDict[act_sched.schedule.id] = {"scheduler": self.scheduler, "actions": self.evt_list}
                print "Schedule '%s' is planned." % db_schedule.name, "Total actions %s" % str(count)
                print("...")
                # single thread version is not suitable for async calls
                # scheduler.run()
                # Start a thread to run the events
                t = threading.Thread(target=self.scheduler.run)
                t.start()
                #anoter wat to play actions
                # threading.Timer()
            else:
                print "Nothing to plan..."
        else:
            print "Schedule '%s' is not active'" % db_schedule.name
        print("Exit from schedule execution method")





    def stop_schedule(self, schedule):
        # Отменяем все, что в Планировщике
        self.force_stop()
        # Поочереди отменяем все, что в статусе "Ожидание" или "В работе" и выключаем ноги
        for act_sched in schedule.actionschedules_set.all():
            self.stop_actsched(act_sched)
        print("Backend.Cancelled")




    # Отмена задач Планировщика python
    def force_stop(self):
        #неверно так прерывать, надо после этого пробежаться по всем шагам и выполнить их
        if self.evt_list != None and self.scheduler != None:
            for e in self.evt_list:
                print "Cancelling"
                self.scheduler.cancel(e)




    # Выключаем ногу, которая в расписании, сообщаем в лог, и статус меняем с "ожидания" на "остановлено"
    def stop_actsched(self, act_sched):
        if act_sched is not None:
            print "Turning off %s pin" % act_sched.action.pin
            command = ["python", "/home/pi/dev/scripts/switch.py", "%s" % act_sched.action.pin, "0"]
            self.do_shell_cmd(command)




    #todo: Добавить проверку, что мы в *nix системе, а дальше просто вызов, чтобы при диплоях каждый раз код не коментить
    def do_shell_cmd(self,cmd_with_params):
        print("Command is executing")
        res = call(cmd_with_params)








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
    # b.exec_schedule(s)
    print "statDict len:%s" % len(b.schedDict)
    val = b.schedDict.get(s.id)
    # print val.get("scheduler").queue

    # print "Now: %s" % time.time(), "Datetime:%s" % s.last_run
    #
    # newTime = timezone.localtime(s.last_run)
    # strTime = str(newTime).replace("+04:00", "")
    # print(strTime)
    # newTime2 = time.strptime(strTime, '%Y-%m-%d %H:%M:%S.%f')
    #
    dt = datetime.datetime.now()
    print dt
    dt2 = datetime.datetime.now() + datetime.timedelta(days=12)
    print dt2
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

    i = 5
    den=3
    for c in range(0,i):
        print "c=%s"% c,"%s" %c, "%", "%s" %den, "=",
        print  c%den