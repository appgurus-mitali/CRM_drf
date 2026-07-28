from .models import Lead,LeadSource,LeadStatus,Priority
from rest_framework import serializers
from django.db.models import Q

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['id','first_name','last_name','email','phone','company_name','description','status','source','priority','assigned_lead','created_at','updated_at','status']
        read_only_fields = ['id','created_at','assigned_lead']
        extra_kwargs = {
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
            'phone':{
                'required':True,
                'allow_null':False,
                "error_messages":{
                    'invalid': 'Please enter a valid numeric phone number with digits only.',
                    'required': 'Phone field is required',
                    'null': 'Phone is required'
                },
                'validators': []
            },
            'source':{
                "error_messages":{
                    'invalid_choice': f'Invalid Source. Please choose a valid choice.Allowed choices: {LeadSource.values}',
                },
            },
            'priority':{
                "error_messages":{
                    'invalid_choice': f'Invalid Priority. Please choose a valid choice.Allowed choices: {Priority.values}',
                },
            },
            'status':{
                "error_messages":{
                    'invalid_choice': f'Invalid status. Please choose a valid choice.Allowed choices: {LeadStatus.values}',
                },
            },
        }

    def validate_phone(self,value):
        if value<6000000000 or value>9999999999:
            raise serializers.ValidationError('Mobile Nmber must be according to valid 10 digit indian Number.')
        return value
    
    def validate(self, attrs):
        # email = attrs.get('email')
        # phone = attrs.get('phone')

        # existing = Lead.objects.filter(Q(email=email) | Q(phone=phone))

        # if self.instance:
        #     existing = existing.exclude(pk=self.instance.pk)

        # errors = {}
        # for user in existing:
        #     if user.email == email:
        #         errors['email'] = "This email is already registered."
        #     if user.phone == phone:
        #         errors['phone'] = "This phone number is already in use."  
        # if errors:
        #     raise serializers.ValidationError(errors)

        return attrs

    