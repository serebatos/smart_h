from django.http.response import Http404
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.http import HttpResponse
from h_ctrl.models import Action, Schedule
from models import Pi
from subprocess import call

# Create your views here.

ACT_TYPE_SINGLE="SINGLE"
ACT_TYPE_SCHEDULE="SCHEDULE"

def index(request):
    pi_list = Pi.objects.all()
    context = {'pi_list': pi_list}
    return render(request, 'h_ctrl/index.html', context)


def detail(request, pi_id):
    try:
        # p = Pi.objects.get(pk=pi_id)
        p = get_object_or_404(Pi, pk=pi_id)
        sch = Schedule.objects.all()
    except Pi.DoesNotExist:
        raise Http404
    return render(request, "h_ctrl/detail.html", {'rasp': p, 'sch_all':sch})


def command(request, pi_id):
    if "q" in request.POST:
        message = 'You searched for: %s' % request.POST['q']
    else:
        message = 'You submitted an empty form. %s' % request

    return HttpResponse(message)

def ajax(request, pi_id):
    message = pi_id
    if request.method == 'POST' and request.is_ajax():
        act_type = request.POST['type']
        if act_type == ACT_TYPE_SINGLE:
            action = request.POST['action']
            if action == 'turn_on':
                call(["python","/home/pi/dev/scripts/led_blink.py"])
            try:
                actObj = get_object_or_404(Action,name=action)
                call(["python","/home/pi/dev/scripts/switch.py","%s" % actObj.pin, "%s" % actObj.cmd_code])
            except Action.DoesNotExist:
                raise  Http404
            message = action + '(' + pi_id +')'
        if act_type==ACT_TYPE_SCHEDULE:
            message="Schedule is activated"
    return HttpResponse(message)
