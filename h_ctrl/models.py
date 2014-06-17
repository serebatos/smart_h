from compiler.ast import name
from django.db import models

# Create your models here.
from django.db.models.fields.related import ManyToOneRel


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

    def __unicode__(self):
        return self.name


class Schedule(models.Model):
    actions = models.ManyToManyField(Action)
    name = models.CharField(max_length=20)
    start_time = models.TimeField(name="Start")
    end_time = models.TimeField(name="End")
    certain_date = models.DateTimeField(name="One time run date")
    run_every_days = models.IntegerField(default=1)

    def __unicode__(self):
        return self.name