__author__ = 'reprintsevsv'
# -*- coding: utf-8 -*-
from h_ctrl.models import Schedule
from h_ctrl.views import *
from django.db.models import Q
from django.db import OperationalError
from h_ctrl.const import *


def run():
    """
    Here we do all necessary initialization stuff

    """
    # todo: startup scheduler
    print("I'm initialized")
    try:
        sched_running = Schedule.objects.filter(Q(status=Const.STATUS_RUNNING))
        be = Backend()
        # То, что работало и было аццки прервано - запускаем заново
        for s in sched_running:
            be.stop_schedule(s)
            s.status = Const.STATUS_PLANNED
            s.save()

        # То, что было в плане - по плану и запускаем в шедулер, до следуюшего ребута или тому подобного
        sched_planned = Schedule.objects.filter(Q(status=Const.STATUS_PLANNED))
        for s in sched_planned:
            be.exec_schedule(s)
    except OperationalError:
        print("OperationalError")


