from django.http.response import Http404, StreamingHttpResponse
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.http import HttpResponse
from backend import Backend
from h_ctrl.models import Action, Schedule
from models import Pi
from subprocess import call
from django.db.models import Q
from h_ctrl.const import *

# Create your views here.


ACT_TYPE_SINGLE = "SINGLE"
ACT_TYPE_SCHEDULE = "SCHEDULE"

RESULT_OK = 0
RESULT_BAD = -1


def index(request):
    pi_list = Pi.objects.all()
    context = {'pi_list': pi_list}
    return render(request, 'h_ctrl/index.html', context)


def detail(request, pi_id):
    try:
        # p = Pi.objects.get(pk=pi_id)
        p = get_object_or_404(Pi, pk=pi_id)
        sch_all = Schedule.objects.all()
        sch_active_list = list()
        ret_list = list()
        ret_list_row = list()
        be = Backend()

        cur_line = 1
        idx_line = 0
        # if len(be.schedDict) > 0:
        # Looping through all schedules
        for s in sch_all:
            idx_line = cur_line % 3
            ret_list_row.append(s)
            if idx_line == 0:
                # add 3 columns per row
                ret_list.append(ret_list_row)
                ret_list_row = list()
            cur_line += 1
        if len(ret_list_row) > 0:
            # add row
            ret_list.append(ret_list_row)
            # print("Searching")
            # sch_details = be.schedDict.get(s.id)
            # if not sch_details == None:
            # sch_active_list.append({"schedule": s, "details": sch_details})
            # print("Appended,"),
            # print sch_details
            # else:
            # print("Empty!!!")


    except Pi.DoesNotExist:
        raise Http404
    return render(request, "h_ctrl/detail.html", {'rasp': p, 'ret_list': ret_list})


def command(request, pi_id):
    if "q" in request.POST:
        message = 'You searched for: %s' % request.POST['q']
    else:
        message = 'You submitted an empty form. %s' % request

    return HttpResponse(message)


def change_schedule_status(sch_id, status):
    schedule = get_object_or_404(Schedule, id=sch_id)
    schedule.status = status
    # save to DB
    schedule.save()
    return schedule


def stop_schedule(request, pi_id):
    be = Backend()
    messsage = {"Error"}
    try:
        sch_id = request.POST['sch_id']
        # # schedule = change_schedule_status(sch_id, STATUS_STOPPED)
        schedule = get_object_or_404(Schedule, id=sch_id)
        be.stop_schedule(schedule)
        messsage = {Const.STATUS_STOPPED}
    except Schedule.DoesNotExist:
        raise Http404
    return HttpResponse(messsage)


def start_schedule(request, pi_id):
    be = Backend()
    messsage = {"Error"}
    try:
        sch_id = request.POST['sch_id']
        # schedule = change_schedule_status(sch_id, STATUS_PLANNED)
        schedule = get_object_or_404(Schedule, id=sch_id)
        # Defense against idiot - do not allow to plan schedule multiple times if now, so process only active schedules
        if schedule.status is not Const.STATUS_RUNNING or schedule.status is not Const.STATUS_PLANNED:
            be.exec_schedule(schedule)
            messsage = {Const.STATUS_PLANNED}
        else:
            messsage = {"Nothing"}
    except Schedule.DoesNotExist:
        raise Http404
    return HttpResponse(messsage)


def sch(request, pi_id):
    print("In sched")
    sch_id = request.POST['sch_id']
    print repr(request.POST)
    action = request.POST['action']
    schedule = Schedule.objects.get(pk=sch_id)
    print "Before action '%s'" % action
    be = Backend()
    print "Backend stat size: %s" % len(be.schedDict)

    if action == "stop":
        status = Const.STATUS_STOPPED
        # cancel currently running schedule and start new
        schedule_current = Schedule.objects.filter(Q(status=Const.STATUS_RUNNING) | Q(status=Const.STATUS_PLANNED))
        if len(schedule_current) > 0:
            print "Got running schedule '%s'" % schedule_current[0]
            schedule_current[0].status = Const.STATUS_STOPPED
            schedule_current[0].save()
            print "Forcing stop scheduler"
            be.stop_schedule(schedule_current[0])
    elif action == "start":
        status = Const.STATUS_RUNNING
        be.exec_schedule(schedule)

    print "Status switched to: %s" % status % ", action: %s" % action
    schedule.status = status
    schedule.save()
    print("Saved")

    message = "Schedule(" + sch_id + ") is %s" % ( "started" if status == Const.STATUS_RUNNING else "stopped")
    print("Message:" + message)
    return HttpResponse(message)


def ajax(request, pi_id):
    message = pi_id
    if request.method == 'POST' and request.is_ajax():
        act_type = request.POST['type']
        print("In ajax:" + act_type)
        if act_type == ACT_TYPE_SINGLE:
            action = request.POST['action']
            if action == 'turn_on':
                call(["python", "/home/pi/dev/scripts/led_blink.py"])
            try:
                actObj = get_object_or_404(Action, name=action)
                command = ["python", "/home/pi/dev/scripts/switch.py", "%s" % actObj.pin, "%s" % actObj.cmd_code]
                res = call(command)
            except Action.DoesNotExist:
                raise Http404
            message = action + '(' + pi_id + ')' + command
        elif act_type == ACT_TYPE_SCHEDULE:
            print("in sched if")
            sch_id = request.POST['sch_id']
            print repr(request.POST)
            action = request.POST['action']

            if action == "stop":
                b = False
            elif action == "start":
                b = True
            sch = Schedule.objects.get(pk=sch_id)
            sch.enabled = b
            sch.save()

            message = "Schedule(" + sch_id + ") is %s" % ( "deactivated" if b == False else "activated")
            print("Message:" + message)

    return HttpResponse(message)
