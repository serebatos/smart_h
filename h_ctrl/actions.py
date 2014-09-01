__author__ = 'reprintsevsv'
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
from django.db.models import Q


def do_action(request, pi_id):
    print repr(request)
    msg = "ok"
    return HttpResponse(request, msg)