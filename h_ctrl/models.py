from django.db import models

# Create your models here.
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
    controller = models.ForeignKey(Pi)
    name = models.CharField(max_length=20)
    pin = models.IntegerField(default=0)
    cmd_code=models.CharField(max_length=1)

    def __unicode__(self):
        return self.name + ":" + self.controller.name


class Schedule(models.Model):
    name = models.CharField(max_length=20)
    # start_time = models.TimeField("Start time")
    # duration = models.IntegerField(default=0)
    # days_repeat=models.IntegerField(default=1) #repeat everyday by default
    # pi=models.ForeignKey(Pi)
    action = models.ManyToManyField(Action)


    def __unicode__(self):
        return self.name
