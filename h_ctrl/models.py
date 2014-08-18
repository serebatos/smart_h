from django.db import models

# Create your models here.
from django.db.models.fields.related import ManyToOneRel
from datetime import date
from django.db.models.fields.related import ManyToManyField, ManyToManyRel


class Home(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class Pi(models.Model):
    parent = models.ForeignKey(Home)
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class Action(models.Model):
    controller = models.ForeignKey(Pi, rel_class=ManyToOneRel)
    name = models.CharField(max_length=20)
    pin = models.IntegerField(default=0)
    cmd_code=models.CharField(max_length=1)
    # schedules = models.ManyToManyField('Schedule', through="ActionSchedules", blank="True")

    def __unicode__(self):
        return self.name + ":" + self.controller.name

class Schedule(models.Model):
    name = models.CharField(max_length=20)
    # start_time = models.TimeField()
    # end_time = models.TimeField()
    # certain_date = models.DateTimeField()
    run_every_days = models.IntegerField(default=1)
    total_runs= models.IntegerField(default=0)
    last_run=models.DateTimeField(auto_now_add=True, blank=True)
    status = models.CharField(max_length=1)
    enabled=models.BooleanField()

    # actions = models.ManyToManyField('Action', through="ActionSchedules", blank="True")
    actions = models.ManyToManyField(Action, through="ActionSchedules", blank="True")
    def __unicode__(self):
        return self.name

class ActionSchedules(models.Model):
    action = models.ForeignKey(Action)
    schedule = models.ForeignKey(Schedule)
    start_time = models.TimeField()
    status=models.CharField(max_length=1)
    comment = models.CharField(max_length=64)
    skip=models.BooleanField("Skip")
    class Meta:
        # db_table = 'store_schedule_actions'
        auto_created = Schedule

# class ActionSchedules(models.Model):
#     schedule = models.ForeignKey(Schedule)
#     action = models.ForeignKey(Action)
#
#     class Meta:
#         db_table = 'store_schedule_actions'
#         auto_created = Schedule