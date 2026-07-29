from rest_framework import serializers
from .models import MyUser,ActivityLog
import re
from datetime import datetime,date
from django.db.models import Q

class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id','username','first_name','last_name','email','mobile','dob','age','gender','password']

        extra_kwargs = {
            'id':{
                'read_only':True,
                'help_text': 'Generated automatically.'
            },
            'age':{
                'read_only':True,
                'help_text': 'Calculated automatically from Date of Birth.'
            },
            'password':{
                'write_only':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your Password',
                    'null': 'Password is required.',
                    'required':"Password field is required."
                }
            },
            'first_name':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your First name.',
                    'null': 'First name field must not be null.',
                    'required':"First name is required."
                }
            },
            'last_name':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your Last name.',
                    'null': 'Last name field must not be null.',
                    'required':"Last name is required."
                }
            },
            'username':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Username is required.',
                    'null': 'Username is required.',
                    'required':"Username field is required.",
                    'unique':"Username already exists."
                },
                'validators': []
            },
            'email':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'invalid': 'Enter a valid Email address dfgsdfgsdg',
                    'blank': 'Email is required.',
                    'null': 'Email field must not be null.',
                    'required':"Email is required."
                },
                'validators': []
            },
            'mobile':{
                'required':True,
                'allow_null':False,
                "error_messages":{
                'invalid': 'Please enter a valid numeric mobile number with digits only.',
                'required': 'Mobile field is required',
                'null': 'Mobile is required'
                },
                'validators': []
            },
            'dob':{
                'required':True,
                'allow_null':False,
                "error_messages":{
                'invalid': 'Please enter a valid Date of birth in YYYY-MM-DD',
                'required': 'Date of Birth field is required.',
                'null': 'Date of Birth is required.'
                },
            }
        }
    
    def validate_password(self,value):
        if len(value)<8:
            raise serializers.ValidationError("Password must be min 8 char long.")
        if not re.search(r"[A-Z]",value):
            raise serializers.ValidationError("Password must contain atleast one upper case letter.")
        return value
    
    def validate_mobile(self,value):
        if value<6000000000 or value>9999999999:
            raise serializers.ValidationError('Mobile Nmber must be according to valid 10 digit indian Number.')
        return value
    
    def validate_dob(self,value):
        if value>=date.today():
            raise serializers.ValidationError('Pls Enter valid Date of birth.')
        return value
    
    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        mobile = attrs.get('mobile')

        existing = MyUser.objects.filter(
            Q(username=username) | Q(email=email) | Q(mobile=mobile)
        )

        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)

        errors = {}
        for user in existing:
            if user.username == username:
                errors['username'] = "This username is already taken."
            if user.email == email:
                errors['email'] = "This email is already registered."
            if user.mobile == mobile:
                errors['mobile'] = "This mobile number is already in use."

        password = attrs.get('password')
        if self.instance and password:
            if not self.instance.check_password(password):
                errors['password'] = "Incorrect password. Profile update denied."

        if errors:
            raise serializers.ValidationError(errors)

        if errors:
            raise serializers.ValidationError(errors)

        dob = attrs.get('dob',None) #or (self.instance.dob if self.instance else None)
        if dob is not None :
            attrs.setdefault("dob",dob)
            today = datetime.now()
            years = today.year - dob.year
            month = today.month - dob.month
            day = today.day - dob.day
            if day<0:
                month-=1
            if month<0:
                years-=1
            self.age = years
            attrs['age'] = years
        return attrs
    
    def create(self, validated_data):
        return MyUser.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # if password is not None:
        #     instance.set_password(password)
        #     instance.save()

        return super().update(instance, validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    # user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'action', 'module', 'object_id', 'description', 'changes', 'created_at']#, 'user_name'