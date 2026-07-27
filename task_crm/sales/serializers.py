from rest_framework import serializers
from .models import Deal, FollowUp, DealStage, FollowUpStatus


class DealSerializer(serializers.ModelSerializer):
    # stage_display = serializers.CharField(source='get_stage_display', read_only=True)
    # assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    # company_name = serializers.CharField(source='company.name', read_only=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'title', 'value', 'stage', # 'stage_display', 
            'expected_close_date', 'company', 'company_name', 
            'contact', 'assigned_to', #'assigned_to_name', 
            'description', 'created_at', 'updated_at'
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
        }



class FollowUpSerializer(serializers.ModelSerializer):
    # type_display = serializers.CharField(source='get_followup_type_display', read_only=True)
    # status_display = serializers.CharField(source='get_status_display', read_only=True)
    # assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            'id', 'title', 'followup_type', 'type_display', 'status', 'status_display',
            'scheduled_at', 'notes', 'lead', 'deal', 'contact', 'company',
            'assigned_to', 'remarks', 'created_at', 'updated_at'#, 'assigned_to_name'
        ]
        read_only_fields = ['id','assigned_to','created-at','updated_at']
    