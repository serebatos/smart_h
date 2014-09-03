__author__ = 'reprintsevsv'
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
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Test
def do_action(request, pi_id):
    try:
        act_id = request.POST['action_id']
    except Exception:
        logger.error("Can't find action ID in request", )
        pass
    print "act_id:%s" % act_id
    try:
        actObj = get_object_or_404(Action, id=act_id)
        be = Backend()
        logger.info("Action: '%s'", actObj.name)
        be.exec_action(actObj)
    except Action.DoesNotExist:
        raise Http404
    logger.info("%s is executed", actObj.name)
    msg = "ok"
    return StreamingHttpResponse( msg)