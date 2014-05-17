from django.http.response import Http404
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.http import HttpResponse
from models import Pi

# Create your views here.



def index(request):
    pi_list = Pi.objects.all()
    context = {'pi_list': pi_list}
    return render(request, 'h_ctrl/index.html', context)


def detail(request, pi_id):
    try:
        # p = Pi.objects.get(pk=pi_id)
        p = get_object_or_404(Pi, pk=pi_id)
    except Pi.DoesNotExist:
        raise Http404
    return render(request, "h_ctrl/detail.html", {'rasp': p})


def command(request, pi_id):
    if "q" in request.POST:
        message = 'You searched for: %s' % request.POST['q']
    else:
        message = 'You submitted an empty form. %s' % request

    return HttpResponse(message)

def ajax(request, pi_id):
    message = pi_id
    if request.method == 'POST' and request.is_ajax():
        name = request.POST['name']
        action = request.POST['city']
        # message = name + ' lives in ' + city + " with pi_id = " + pi_id
        message = action
    return HttpResponse(message)
