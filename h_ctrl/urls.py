from django.conf.urls import patterns, url

from h_ctrl import views
from h_ctrl import simple_actions
from h_ctrl import actions

urlpatterns = patterns('',
    # ex: /h_ctrls/
    url(r'^$', views.index, name='index'),
    url(r'^(?P<pi_id>\d+)/$', views.detail, name='detail'),
    url(r'^(?P<pi_id>\d+)/do/$', views.command, name='command'),
    url(r'^(?P<pi_id>\d+)/ajax/$', views.ajax, name='ajax'),
    url(r'^(?P<pi_id>\d+)/sch/$', views.sch, name='sch'),
    url(r'^(?P<pi_id>\d+)/start_schedule/$', views.start_schedule, name='start_sch'),
    url(r'^(?P<pi_id>\d+)/stop_schedule/$', views.stop_schedule, name='stop_sch'),
    url(r'^(?P<pi_id>\d+)/do_action/$', actions.do_action, name='do_act'),
    url(r'^actions/$', simple_actions.get_index, name='simple'),
    url(r'^actions/post$', simple_actions.action, name='simple_act')

)