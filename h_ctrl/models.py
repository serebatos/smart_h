from django.db import models

# Create your models here.


class Pi(models.Model):
    name = models.CharField(max_length=20)
    period = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name


class Action(models.Model):
    schedule = models.ForeignKey(Pi)
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name
