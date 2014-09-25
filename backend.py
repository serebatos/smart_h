# coding=utf-8
__author__ = 'Serebatos'

import threading
import SocketServer
import os
import pickle
import sched
import time
import datetime
import logging
from subprocess import call
from django.utils import timezone
from h_ctrl.const import *


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_h.settings")
from h_ctrl.models import Action, ActionSchedules, Schedule, Pi, Home


class Backend(object):
    logger = logging.getLogger(__name__)
    schedDict = dict()
    scheduler = sched.scheduler(time.time, time.sleep)
    evt_list = list()

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Backend, cls).__new__(cls)
        return cls.instance

    # Выполнение события, запланированного через штатный шедулер, не путать с exec_action
    def exec_event(self, actionschedules, prev_actionschedules):
        # Делаем декремент счетчика
        details = Backend.schedDict.get(actionschedules.schedule_id)
        details['count'] -= 1
        self.logger.info("Action '%s', count is %s", actionschedules.action.name, details['count'])
        if details['count'] == 0:
            last_event = True
        else:
            last_event = False
        # Уменьшили счетчик, положили обратно в словарь
        Backend.schedDict[actionschedules.schedule_id] = details

        # Проверка на проставленность флага "Пропуск"
        if actionschedules.skip is False and actionschedules.schedule.enabled is True:
            self.logger.info("%s Running '{%s}'", datetime.datetime.now(), actionschedules.action.name)

            actualAction = Action.objects.get(pk=actionschedules.action.id)
            self.exec_action(actualAction)

            if last_event is True:
                actionschedules.status = Const.ACT_STOPPED
                # Запуск плнирования по новой отсюда не подходит, т.к. если шаг помечен как "пропущенны",
                # то все сломается
            else:
                actionschedules.status = Const.ACT_RUNNING
            actionschedules.save()

            self.logger.info("Backend. Status saved")

            if prev_actionschedules is not None:
                prev_actionschedules.status = Const.ACT_STOPPED
                prev_actionschedules.save()

        # Пропускаем действие
        else:
            self.logger.info(unicode("Skipping {}".format(actionschedules.action.name)))

        # Обновляем время последней активности по данному расписанию
        db_schedule = Schedule.objects.get(pk=actionschedules.schedule.id)
        db_schedule.last_run = datetime.datetime.now()
        db_schedule.save()

        # На последнем действии, даже если оно пропущено, заново инициализируем правило
        if last_event is True:
            self.exec_schedule(actionschedules.schedule)

    # Выполнение действия(управление ногой, например)
    def exec_action(self, action):
        try:
            self.set_pin(action.pin, action.cmd_code)
        except Exception:
            self.logger.exception("Exception in exec_action")

    def repeat_schedule(self, schedule):
        return ""

    def exec_schedule(self, schedule):
        db_schedule = Schedule.objects.get(pk=schedule.id)
        prev_act_sch = None  # previous action which status should be changed to "Completed"
        count = 0
        act_list = list()
        delta_starttime = None
        prev_starttime = None
        dtstart = datetime.datetime.now()

        dcur = datetime.datetime.now()

        self.logger.info("Executing rule '%s'", db_schedule.name)
        if db_schedule.enabled is True:
            # Создаем шедулер
            self.scheduler = sched.scheduler(time.time, time.sleep)
            # Инициализируем список
            self.evt_list = act_list
            self.logger.info("Logging before planning events")

            for act_sched in db_schedule.actionschedules_set.all():
                self.logger.info("'%s' is being putted in queue. Start time is %s", act_sched.action.name,
                                 act_sched.start_time)
                # Текущее время
                if db_schedule.status == Const.STATUS_STOPPED or db_schedule.status == None:
                    tcur = time.time() #todo: под никсами со временем какая-то херь, оно как будто не текушее
                    self.logger.info("Starting as new. tcur = '%s", tcur)
                elif db_schedule.status == Const.STATUS_RUNNING or db_schedule.status == Const.STATUS_PLANNED:
                    tcur = db_schedule.last_run
                    self.logger.info("Restarting as already started. tcur=", tcur)

                dcur = datetime.datetime.combine(dcur.date(), act_sched.start_time)
                # Планируемое время запуска
                tt = time.mktime(
                    (dcur.year, dcur.month, dcur.day, act_sched.start_time.hour, act_sched.start_time.minute,
                     act_sched.start_time.second, dcur.weekday(), dcur.timetuple().tm_yday, -1))

                dtstart = dcur

                self.logger.info("Analyzing previous start time. tt ='%s'", tt)

                if prev_starttime is None:

                    if tcur > tt:
                        self.logger.info("Backend. Start time of action( %s - %s )is in the past.", schedule.name,
                                         act_sched.action.name)
                    while tcur > tt:
                        # self.logger.info("In loop")
                        # Поле last_run надо менять, наверное, по запуску или действительно вводить поля плановое время
                        # запуска, чтобы корректно планировать запуск
                        dtstart = dcur + datetime.timedelta(minutes=db_schedule.run_every)
                        tt = time.mktime((dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute,
                                          dtstart.second, dtstart.weekday(), dtstart.timetuple().tm_yday, -1))
                        # self.logger.info("Backend. Start time is in the past. Planning this action(%s) on %s",
                        # act_sched.action.name, dtstart)
                        dcur = dtstart

                else:
                    self.logger.info("Calculating start time according previous activity start time")
                    m_dcur = datetime.datetime.combine(datetime.datetime.now(), prev_act_sch.start_time)
                    self.logger.info("Prev Act start time is '%s'", m_dcur)
                    m_dcur2 = datetime.datetime.combine(datetime.datetime.now(), act_sched.start_time)
                    self.logger.info("Cur Act start time is '%s'", m_dcur2)
                    dt2 = m_dcur2 - m_dcur
                    self.logger.info("Delta is '%s'", dt2)
                    dtstart = prev_starttime + dt2
                    self.logger.info("DTStart is '%s'", dtstart)
                    tt = time.mktime((dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute,
                                      dtstart.second, dtstart.weekday(), dtstart.timetuple().tm_yday, -1))

                prev_starttime = dtstart
                self.logger.info("'%s' is planned on %s, prevtime is set to '%s'", act_sched.action.name, dtstart, prev_starttime)

                # planned event - crucial moment in the whole project ^^
                event_sched = self.scheduler.enterabs(tt, 1, self.exec_event, (act_sched, prev_act_sch))

                # Статус в "Ожидание" выполнения
                act_sched.status = Const.ACT_WAITING
                act_sched.save()

                # collected to list
                self.evt_list.append(event_sched)
                prev_act_sch = act_sched
                count += 1

            if count > 0:
                self.schedDict[act_sched.schedule.id] = {"scheduler": self.scheduler, "actions": self.evt_list,
                                                         "count": count}
                self.logger.info("Schedule '%s' is planned. Total actions %s", db_schedule.name, str(count))
                self.logger.info("...")

                # single thread version is not suitable for async calls
                # scheduler.run()

                # Start a thread to run the events
                t = threading.Thread(target=self.scheduler.run)
                t.start()

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
        self.logger.info("In stop")
        # Отменяем все, что в Планировщике
        self.force_stop()
        self.logger.info("Self scheduler is cancelled")
        # Поочереди отменяем все, что в статусе "Ожидание" или "В работе" и выключаем ноги
        for act_sched in schedule.actionschedules_set.all():
            self.logger.info("Turning off (%s - %s)", schedule.name, act_sched.action.name)
            self.stop_actsched(act_sched)
            act_sched.status = 'S'
            act_sched.save()
        self.logger.info("Backend.Cancelled")


    # Отмена задач Планировщика python
    def force_stop(self):
        # неверно так прерывать, надо после этого пробежаться по всем шагам и выполнить их
        if self.evt_list is not None and self.scheduler is not None:
            self.logger.info("Starting loop to Cancel all events")
            for e in self.evt_list:
                try:
                    if self.scheduler is not None:
                        self.logger.info("Cancelling %s", e)
                        self.scheduler.cancel(e)
                except:
                    self.logger.exception("Exception")
                self.logger.info("Cancelling %s - OK", e)


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
    # b = Backend()
    # s = Schedule.objects.get(pk=1)
    # print "b={}".format(str(b.c))
    # b.exec_schedule(s)
    # print "statDict len:%s" % len(b.schedDict)
    # val = b.schedDict.get(s.id)
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
    tcur = time.time()
    dcur = datetime.datetime.now()
    dtstart = dcur
    tt = time.mktime((dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute,
                      dtstart.second, dtstart.weekday(), dtstart.timetuple().tm_yday, -1))
    print(tcur)
    print(dtstart)
    print(tt)
    dtstart = dcur + datetime.timedelta(minutes=10)
    tt = time.mktime((dtstart.year, dtstart.month, dtstart.day, dtstart.hour, dtstart.minute,
                      dtstart.second, dtstart.weekday(), dtstart.timetuple().tm_yday, -1))
    print(dtstart)
    print(tt)
    print (tcur - tt)

    # schedDict = dict()
    # schedDict[1] = {"scheduler": "test", "actions": "actions", "count": 1}
    # print repr(schedDict[1])
    # details = schedDict[1]
    # print repr(details)
    # print(details['count'])
    # details['count']+=1
    # schedDict[1] = details
    # print repr(details)
