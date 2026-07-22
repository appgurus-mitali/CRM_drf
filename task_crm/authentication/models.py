from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class MyUser(AbstractUser):
    email = models.EmailField(null=False,unique=True)
    username = models.CharField(null=False,blank=False,unique=True)
    mobile = models.BigIntegerField(null=False,blank=False,unique=True)#max_digits=10,blank=False,null=False
    gender = models.CharField(choices=[('male','male'),('female','female'),('not applicable','not applicable')],null=True)
    dob = models.DateField(null=False)
    age = models.SmallIntegerField(null=False)
    created_at = models.DateField(auto_now=True)
