from django.conf.urls import patterns, url

from h_ctrl import views

urlpatterns = patterns('',
    # ex: /h_ctrls/
    url(r'^$', views.index, name='index'),
    url(r'^(?P<pi_id>\d+)/$', views.detail, name='detail'),
    url(r'^(?P<pi_id>\d+)/do/$', views.command, name='command'),
    url(r'^(?P<pi_id>\d+)/ajax/$', views.ajax, name='ajax'),
)