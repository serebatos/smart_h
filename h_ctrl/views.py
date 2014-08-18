from django.http.response import Http404
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.http import HttpResponse
from backend import Backend
from h_ctrl.models import Action, Schedule
from models import Pi
from subprocess import call

# Create your views here.

ACT_TYPE_SINGLE = "SINGLE"
ACT_TYPE_SCHEDULE = "SCHEDULE"


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
        be = Backend()
        if len(be.schedDict) > 0:
            for s in sch_all:
                print("Searching")
                sch_details = be.schedDict.get(s.id)
                if not sch_details == None:
                    sch_active_list.append({"schedule": s, "details": sch_details})
                    print("Appended")
        else:
            print("Empty")

    except Pi.DoesNotExist:
        raise Http404
    return render(request, "h_ctrl/detail.html", {'rasp': p, 'sch_all': sch_all,'sch_act_all':sch_active_list})


def command(request, pi_id):
    if "q" in request.POST:
        message = 'You searched for: %s' % request.POST['q']
    else:
        message = 'You submitted an empty form. %s' % request

    return HttpResponse(message)


def sch(request, pi_id):
    print("In sched")
    sch_id = request.POST['sch_id']
    print repr(request.POST)
    action = request.POST['action']
    schedule = Schedule.objects.get(pk=sch_id)
    if action == "stop":
        b = False
    elif action == "start":
        b = True
        schedule.enabled = b
        schedule.save()
        print("Saved")
        be = Backend()
        print "Backend stat size: %s" % len(be.schedDict)
        be.exec_schedule(schedule)

    message = "Schedule(" + sch_id + ") is %s" % ( "deactivated" if b == False else "activated")
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
