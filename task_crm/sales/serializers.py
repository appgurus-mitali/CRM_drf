from rest_framework import serializers
from .models import Deal, FollowUp, DealStage, FollowUpStatus,FollowUpType


class DealSerializer(serializers.ModelSerializer):
    # stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    # assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    # company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'value', 'stage', # 'stage_display', 
            'expected_close_date', 'company', #'company_name', 
            'contact', 'assigned_to', #'assigned_to_name', 
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id','company','assigned_to','created-at','updated_at','company']

        extra_kwargs = {
            'title':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your Title',
                    'null': 'Title field must not be null.',
                    'required':"Title is required."
                }
            },
            'value':{
                'required':True,
                'allow_null':False,
                "error_messages":{
                'invalid': 'Please enter a valid numeric deal value with digits only.',
                'required': 'value field is required',
                'null': 'value is required'
                },
                'validators': []
            },
            'stage':{
                "error_messages":{
                    'invalid_choice': f'Invalid Source. Please choose a valid choice.Allowed choices: {DealStage.values}',
                },
            },
            'expected_close_date':{
                'required':True,
                'allow_null':False,
                "error_messages":{
                    'invalid': 'Please enter a valid Date of birth in YYYY-MM-DD',
                    'required': 'Expected Date is required.',
                    'null': 'Expected Date is required.'
                },
            },
            'contact':{
                'required':True,
                'allow_null':False,
                'error_messages': {
                    'invalid': 'Please enter a valid contact details',
                    'null': 'contact is required.',
                    'required':"contact is required.",
                    'does_not_exist': 'Please enter a valid contact.',
                }
            },
            
        }

class FollowUpSerializer(serializers.ModelSerializer):
    # type_display = serializers.CharField(source='get_followup_type_display', read_only=True)
    # status_display = serializers.CharField(source='get_status_display', read_only=True)
    # assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            'id', 'title', 'followup_type', 'status', #'status_display',, 'type_display'
            'scheduled_at', 'description', 'lead', 'deal', 'contact', 'company',
            'assigned_to', 'remarks', 'created_at', 'updated_at'#, 'assigned_to_name'
        ]
        read_only_fields = ['id','assigned_to','created-at','updated_at']
        extra_kwargs = {
            'title':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your Title',
                    'null': 'Title field must not be null.',
                    'required':"Title is required."
                }
            },
            'scheduled_at':{
                    'required':True,
                    'allow_null':False,
                    "error_messages":{
                        'invalid': 'Please enter a valid Time of birth in YYYY-MM-DD HH:MM:SS',
                        'required': 'Expected Date is required.',
                        'null': 'Expected Date is required.'
                },
            },
            'status':{
                "error_messages":{
                    'invalid_choice': f'Invalid Status. Please choose a valid choice.Allowed choices: {FollowUpStatus.values}',
                },
            },
            'followup_type':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your Title',
                    'null': 'Title field must not be null.',
                    'required':"Title is required.",
                    'invalid_choice': f'Invalid Type. Please choose a valid choice.Allowed choices: {FollowUpType.values}',
                }
            },
            'lead':{
                'error_messages': {
                    'does_not_exist': 'Please enter a valid lead.',
                    'incorrect_type': 'Please enter a valid lead id.',
                }
            },
        }
        

    