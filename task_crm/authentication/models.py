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

class ActivityAction(models.TextChoices):
    LOGIN = "LOGIN", "Login"
    LOGOUT = "LOGOUT", "Logout"

    CREATE = "CREATE", "Create"
    UPDATE = "UPDATE", "Update"
    DELETE = "DELETE", "Delete"

    ASSIGN = "ASSIGN", "Assign"
    CONVERT = "CONVERT", "Convert"

    CHANGE_PASSWORD = "CHANGE_PASSWORD", "Change Password"


class ActivityModule(models.TextChoices):
    USER = "USER", "User"
    LEAD = "LEAD", "Lead"
    CONTACT = "CONTACT", "Contact"
    COMPANY = "COMPANY", "Company"
    DEAL = "DEAL", "Deal"
    FOLLOWUP = "FOLLOWUP", "Follow Up"
    NOTE = "NOTE", "Note"


class ActivityLog(models.Model):
    user = models.ForeignKey(MyUser,on_delete=models.SET_NULL,related_name="activities",null=True, blank=True)#,null=True

    module = models.CharField(max_length=20,choices=ActivityModule.choices)
    action = models.CharField(max_length=30,choices=ActivityAction.choices)

    object_id = models.PositiveIntegerField(null=True, blank=True)
    changes = models.JSONField(null=True, blank=True)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} {self.action} {self.module}"