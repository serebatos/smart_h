from django.contrib import admin
from h_ctrl.models import Pi, Action, Home, Schedule
# Register your models here.


admin.site.register(Home)
admin.site.register(Pi)
admin.site.register(Action)
admin.site.register(Schedule)


