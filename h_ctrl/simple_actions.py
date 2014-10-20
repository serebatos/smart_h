from django.http import StreamingHttpResponse
from django.shortcuts import render
import logging
from backend import Backend

__author__ = 'bonecrusher'

logger = logging.getLogger(__name__)


def get_index(request):
    message = 'Test'

    return render(request, 'h_ctrl/simple_actions.html', message)

def action(request):
    logger.info("Test")
    val = request.POST['val']
    be = Backend()
    be.set_pin(26, val)
    return StreamingHttpResponse("ok")
