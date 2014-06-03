from django.db import models

# Create your models here.


class Home(models.Model):
    name = models.CharField(max_length=20)



class Pi(models.Model):
    parent = models.ForeignKey(Home)
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class Action(models.Model):
    controller = models.ForeignKey(Pi)
    name = models.CharField(max_length=20)
    pin = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name
