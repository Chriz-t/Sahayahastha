from django.db import models
from mongoengine import Document, StringField, IntField

# Create your models here.


class District(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class Camps(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    volunteerNeeded = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
class Task(models.Model):
    taskId = IntField(required=True, unique=True)
    desc = StringField(required=True)
    status = StringField(default="Pending")
    volunteerId = StringField(required=True)

    def __str__(self):
        return self.desc