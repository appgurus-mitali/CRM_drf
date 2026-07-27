from .serializer import MyUserSerializer,ActivityLogSerializer
from .models import MyUser,ActivityLog,ActivityAction,ActivityModule
from .activities import log_activity

import traceback
import re

from django.db.models import Q

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.
@api_view(['POST'])
def register(request):
    try:
        serializer = MyUserSerializer(data = request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_activity(user=user, module=ActivityModule.USER,action=ActivityAction.CREATE, object_id=user.id,description=f"User account created for '{user.username}'")
            return Response({'status':1,'message':'User Created Successfully.','data':serializer.data},status=status.HTTP_201_CREATED)
        errors={key:err[0] for key,err in serializer.errors.items()}
        return Response({'status':0,'message':'Validation failed.','error':errors},status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print("\n\nException in reg")
        traceback.print_exc()
        return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def login(request):
    try:
        errors = dict()

        username_email = request.data.get("username_email",None)
        if username_email is None or username_email=="":
            errors['username_email']="Username or Email is required."

        password = request.data.get("password",None)
        if password is None or password=="":
            errors['password']="Password is required."

        if len(errors)>0:
            return Response({'status':0,"message":"Invalid data.","errors":errors}, status=status.HTTP_400_BAD_REQUEST)

        user = MyUser.objects.get(Q(username = username_email.strip())|Q(email=username_email.strip()))

        if user:
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                print(user)
                refresh["email"] = user.email
                refresh["username"] = user.username
                log_activity(user=user,module=ActivityModule.USER,action=ActivityAction.LOGIN,object_id=user.id,description=f"User '{user.username}' logged in successfully.")

                return Response({'status':1,"message":f'login successful. Welcome {user.username}',"data":{'access': str(refresh.access_token),'refresh': str(refresh),}}, status=status.HTTP_200_OK)

            return Response({'status':0,'message':"Invalid credentials.","data":{}},status=status.HTTP_401_UNAUTHORIZED)
    except (MyUser.DoesNotExist,MyUser.MultipleObjectsReturned) :
        return Response({'status':0,"message":"User does not exists.","data":[]},status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        traceback.print_exc()
        return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET','PUT','PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method=='GET':
        try:
            serializer = MyUserSerializer(request.user)
            return Response({'status':1,'message':f'Welcome {request.user.username}','data':serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
        return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method in ['PUT','PATCH']:
        try:
            # user = MyUser.objects.get(id= request.user.id)
            user = request.user
            serializer = MyUserSerializer(user,data = request.data,partial=(request.method=='PATCH'))
            if serializer.is_valid():
                updated_user = serializer.save()

                # changes = {}
                # for field, old_val in user.items():
                #     new_val = getattr(updated_user, field)
                #     if old_val != new_val:
                #         changes[field] = {'from': old_val, 'to': new_val}

                log_activity(user=updated_user,module=ActivityModule.USER,action=ActivityAction.UPDATE,
                            object_id=updated_user.id,description="Updated profile information.")#,changes=changes if changes else None)
                return Response({'status':1,'message':f'Profile Details updated Successfully.','data':serializer.data},status=status.HTTP_202_ACCEPTED)
            errors={key:err[0] for key,err in serializer.errors.items()}
            return Response({'status':0,'message':'Validation failed.','error':errors},status=status.HTTP_400_BAD_REQUEST)
        except (MyUser.DoesNotExist,MyUser.MultipleObjectsReturned):
            return Response({'status':0,'message':f'User not exists.','data':{}},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
            return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method =='DELETE':
        try:
            # user = MyUser.objects.get(id = request.user.id)
            user = request.user
            log_activity(user=updated_user,module=ActivityModule.USER,action=ActivityAction.DELETE,
                                        object_id=user.id,description="User profile deleted.")
            user.delete()
            return Response({'status':1,'message':"Account deleted Successfully.",'data':{}},status=status.HTTP_200_OK)
        
        except (MyUser.DoesNotExist,MyUser.MultipleObjectsReturned):
            return Response({'status':0,'message':f'User not exists.','data':{}},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
            return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    try:
        user = request.user
        data = request.data

        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        errors = {}

        if not old_password:
            errors['old_password'] = "Old password is required."
        if not new_password:
            errors['new_password'] = "New password is required."
        else :
            if len(new_password)<8:
                errors['new_password'] = "Password must be 8 char long."
            elif not re.search(r"[A-Z]",new_password):
                errors['new_password'] = "Password must contain atleast one upper case letter."
        if not confirm_password:
            errors['confirm_password'] = "Please confirm your new password."
        
        if errors:
            return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            errors['old_password'] = "Your old password was entered incorrectly."

        if new_password != confirm_password:
            errors['confirm_password'] = "New password and confirmation password do not match."

        if old_password == new_password:
            errors['new_password'] = "New password cannot be the same as your old password."

        if errors:return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        log_activity(
            user=user,
            module=ActivityModule.USER,
            action=ActivityAction.CHANGE_PASSWORD,
            object_id=user.id,
            change = {'password': old_password, 'to': new_password},
            description="User updated their password."
        )
        return Response({'status': 1,'message': 'Password changed successfully. Please log in with your new password.','data': {}},status=status.HTTP_200_OK)

    except Exception:
        traceback.print_exc()
        return Response({'status': 0, 'message': 'An Internal Server Error Occurred.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_feed_view(request):
    """
    GET: Retrieve recent activity feed.
    Optional filters: ?user_id=1 or ?entity_type=Deal
    """
    try:
        # Strictly filter logs belonging ONLY to request.user
        logs = ActivityLog.objects.filter(user=request.user)

        # Optional filter by module (e.g. ?module=DEAL)
        # module_param = request.query_params.get('module')
        # if module_param:
        #     logs = logs.filter(module=module_param.upper())

        # # Return latest 50 records
        # logs = logs[:50]

        serializer = ActivityLogSerializer(logs, many=True)
        return Response(
            {
                'status': 1,
                'message': 'Your activity logs retrieved successfully.',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception:
        return Response(
            {'status': 0, 'message': 'An internal server error occurred.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )