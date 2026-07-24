from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class MyUser(AbstractUser):
    username = models.CharField(null=False,blank=False,unique=True)
    mobile = models.BigIntegerField(null=False,blank=False,unique=True)
    gender = models.CharField(choices=[('male','male'),('female','female'),('not applicable','not applicable')],null=True)
    dob = models.DateField(null=False)
    age = models.SmallIntegerField(null=False)
    created_at = models.DateTimeField(auto_now=True)
