from .models import ActivityLog
from django.contrib.auth.models import AnonymousUser

def log_activity( module, action, description, object_id=None, changes=None,user = None):#, request=None
    # if isinstance(user,AnonymousUser):
    #     user = None
    acti = ActivityLog.objects.create(user=user,module=module,action=action,object_id=object_id,description=description,changes=changes)
    # print(acti)
    return True
