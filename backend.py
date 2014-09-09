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
import logging
from subprocess import call
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_h.settings")
from h_ctrl.models import Action, ActionSchedules, Schedule, Pi, Home


class Backend(object):
    c = 0
    logger = logging.getLogger(__name__)
    schedDict = dict()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Backend, cls).__new__(cls)
        return cls.instance

    # Выполнение события, запланированного через штатный шедулер, не путать с exec_action
    def exec_event(self, actionschedules, prev_actionschedules):
        Backend.c -= 1
        if Backend.c == 0:
            last_event = True
        else:
            last_event = False
        # Проверка на проставленность флага "Пропуск"
        if actionschedules.skip is False and actionschedules.schedule.enabled is True:
            self.logger.info("%s Running action {%s}", time.time(), actionschedules.action.name)

            actualAction = Action.objects.get(pk=actionschedules.action.id)
            self.exec_action(actualAction)

            if last_event is True:
                actionschedules.status = ACT_STOPPED
                self.exec_schedule(actionschedules.schedule)
            else:
                actionschedules.status = ACT_RUNNING
            actionschedules.save()

            self.logger.info("Backend. Status saved")

            if prev_actionschedules is not None:
                prev_actionschedules.status = ACT_STOPPED
                prev_actionschedules.save()

        # Пропускаем действие
        else:
            self.logger.info(unicode("Skipping action {}".format(actionschedules.action.name)))
            # todo: как сделать,чтобы после перезапуска распбери все работало и как сделать повторение на след день,
            # как вариант последний шаг заново инициализирует на следующий день шедулер
        # event_index = self.evt_list.index(actionschedules)
        # self.logger.info("Event: %s, index: %s, total: %s",actionschedules,event_index,len(self.evt_list))
        #



        # Обновляем время последней активности по данному расписанию
        db_schedule = Schedule.objects.get(pk=actionschedules.schedule.id)
        db_schedule.last_run = datetime.datetime.now()
        db_schedule.save()


    # Выполнение действия(управление ногой, например)
    def exec_action(self, action):
        self.set_pin(action.pin, action.cmd_code)
        # command = ["python", "/home/pi/dev/scripts/switch.py", "%s" % actObj.pin, "%s" % actObj.cmd_code]
        # res = call(command)

    def repeat_schedule(self, schedule):
        return ""

    def exec_schedule(self, schedule):
        db_schedule = Schedule.objects.get(pk=schedule.id)
        self.logger.info("Executing rule '%s'", db_schedule.name)
        if db_schedule.enabled == True:

            prev_act_sch = None  # previous action which status should be changed to "Completed'
            count = 0
            act_list = list()
            self.scheduler = sched.scheduler(time.time, time.sleep)
            self.evt_list = act_list

            self.logger.info("Logging before planning events")
            print repr(self.scheduler._queue)
            print (len(self.evt_list))

            dt = datetime.datetime.now()
            self.logger.info("Planning events")
            for act_sched in db_schedule.actionschedules_set.all():
                self.logger.info("Action '%s' is being putted in queue. Start time is %s", act_sched.action.name,
                                 act_sched.start_time)

                # time_float = (act_sched.start_time - newTime.utcfromtimestamp(14400)).total_seconds()
                tcur = time.time()
                tt = time.mktime((dt.year, dt.month, dt.day, act_sched.start_time.hour, act_sched.start_time.minute,
                                  act_sched.start_time.second, dt.weekday(), dt.timetuple().tm_yday, -1))
                # todo: add planned start time to act_sched
                if tcur > tt:
                    dt = dt.combine(dt.date(), act_sched.start_time)
                    dtstart = dt + datetime.timedelta(days=1)
                    tt = time.mktime((dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute,
                                      dtstart.second, dtstart.weekday(), dtstart.timetuple().tm_yday, -1))
                    self.logger.info("Backend. Start time is in the past. Planning this action(%s) on %s",
                                     act_sched.action.name, dtstart)

                # planned event - crucial moment in the whole project ^^
                event_sched = self.scheduler.enterabs(tt, 1, self.exec_event, (act_sched, prev_act_sch))

                # Статус в "Ожидание" выполнения
                act_sched.status = ACT_WAITING
                act_sched.save()

                # collected to list
                self.evt_list.append(event_sched)
                prev_act_sch = act_sched
                count += 1
            if count > 0:
                self.schedDict[act_sched.schedule.id] = {"scheduler": self.scheduler, "actions": self.evt_list}
                self.logger.info("Schedule '%s' is planned. Total actions %s", db_schedule.name, str(count))
                self.logger.info("...")
                # single thread version is not suitable for async calls
                # scheduler.run()

                # Start a thread to run the events
                t = threading.Thread(target=self.scheduler.run)
                t.start()
                Backend.c = count

                # anoter wat to play actions
                # threading.Timer()
                self.logger.info("Logging total planned events")
                print repr(self.evt_list)
            elif count == 1:
                self.logger.warn("Only 1 action")
            else:
                self.logger.info("Nothing to plan...")
        else:
            self.logger.info("Schedule '%s' is not active'", db_schedule.name)
        self.logger.info("Exit from schedule execution method")


    def stop_schedule(self, schedule):
        # Отменяем все, что в Планировщике
        self.force_stop()
        self.logger.info("Self scheduler is cancelled")
        # Поочереди отменяем все, что в статусе "Ожидание" или "В работе" и выключаем ноги
        for act_sched in schedule.actionschedules_set.all():
            self.stop_actsched(act_sched)
        self.logger.info("Backend.Cancelled")


    # Отмена задач Планировщика python
    def force_stop(self):
        # неверно так прерывать, надо после этого пробежаться по всем шагам и выполнить их
        if self.evt_list != None and self.scheduler != None:
            for e in self.evt_list:
                self.logger.info("Cancelling(%s)", e)
                self.scheduler.cancel(e)
                self.logger.info("Cancelling(%s) - OK")


    # Выключаем ногу, которая в расписании, сообщаем в лог, и статус меняем с "ожидания" на "остановлено"
    def stop_actsched(self, act_sched):
        if act_sched is not None:
            self.logger.info("Turning off %s pin", act_sched.action.pin)
            self.set_pin(act_sched.action.pin, "0")


    # Проверку, что мы в *nix системе или нет, надо делать перед формированием команды...
    def do_shell_cmd(self, cmd_with_params):
        self.logger.info("Command is executing")
        res = call(cmd_with_params)


    def set_pin(self, pin, val):
        # Проверка, в какой ОС
        isLinux = False
        self.logger.info("Checking Operating System")
        if isLinux == True:
            command = ["python", "/home/pi/dev/scripts/switch.py", "%s" % pin, val]
            self.do_shell_cmd(command)
        else:
            self.logger.info("Command for pin:%s, val:%s", pin, val)


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
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
    # count = 0
    #
    # def __init__(self, request, client_address, server):
    # MyTCPHandler.count = MyTCPHandler.count+1
    # print "n={}".format(MyTCPHandler.count)
    # SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
    #
    #
    # def handle(self):
    # # self.rfile is a file-like object created by the handler;
    # # we can now use e.g. readline() instead of raw recv() calls
    #
    # self.data = self.rfile.readline().strip()
    # print "{} wrote!:".format(self.client_address[0])
    # print self.data
    # # Likewise, self.wfile is a file-like object used to write back
    # # to the client
    # self.wfile.write(self.data.upper())

    i = 5
    den = 3
    for c in range(0, i):
        print "c=%s" % c, "%s" % c, "%", "%s" % den, "=",
        print  c % den