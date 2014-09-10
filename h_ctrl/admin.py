from django.contrib import admin
from h_ctrl.models import Pi, Action, Home, Schedule, ActionSchedules
# Register your models here.
# class ActionAdmin(admin.ModelAdmin):
#     list_filter = ['schedules']
#     filter_horizontal = ['schedules']

class ActionSchedulesInline(admin.TabularInline):
    model = Schedule.actions.through
    readonly_fields = ["planned_start_time"]
    extra = 1

class ScheduleAdmin(admin.ModelAdmin):
    inlines = (ActionSchedulesInline,)
    exclude = ["actions"]
    readonly_fields = ["total_runs", "last_run", "status"]
# # fields = (("start_time","end_time"),"certain_date")
#     list_filter = ['actions']
#     filter_horizontal = ['actions']
#
#
admin.site.register(Schedule, ScheduleAdmin)
# admin.site.register(Action, ActionAdmin)

admin.site.register(Home)
admin.site.register(Pi)
admin.site.register(Action)
admin.site.register(ActionSchedules)


