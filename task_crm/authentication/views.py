from .serializer import MyUserSerializer
from .models import MyUser

import traceback

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
            serializer.save()
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

        username_email = request.data.get("username_email")
        if username_email is None or username_email=="":
            errors['username_email']="Username or Email is required."

        password = request.data.get("password",None)
        if password is None or password=="":
            errors['password']="Password is required."

        if len(errors)>0:
            return Response({'status':1,"message":"Invalid data.","errors":errors}, status=status.HTTP_400_BAD_REQUEST)

        user = MyUser.objects.get(Q(username = username_email.strip())|Q(email=username_email.strip()))

        if user:
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                print(user)
                refresh["email"] = user.email
                refresh["username"] = user.username
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
            user = MyUser.objects.get(id= request.user.id)
            serializer = MyUserSerializer(user,data = request.data,partial=(request.method=='PATCH'))
            if serializer.is_valid():
                serializer.save()
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
            user = MyUser.objects.get(id = request.user.id)
            user.delete()
            return Response({'status':1,'message':"Account deleted Successfully.",'data':{}},status=status.HTTP_200_OK)
        
        except (MyUser.DoesNotExist,MyUser.MultipleObjectsReturned):
            return Response({'status':0,'message':f'User not exists.','data':{}},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
            return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    