from rest_framework import serializers
from .models import Deal, FollowUp, DealStage, FollowUpStatus,FollowUpType,Note,EntityType
from customer.models import Company,Contact
from lead.models import Lead


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
        read_only_fields = ['id','company','assigned_to','created_at','updated_at','company']

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
            'contact':{
                'error_messages': {
                    'does_not_exist': 'Please enter a valid contact.',
                    'incorrect_type': 'Please enter a valid contact id.',
                }
            },
            'company':{
                'error_messages': {
                    'does_not_exist': 'Please enter a valid company.',
                    'incorrect_type': 'Please enter a valid company id.',
                }
            },
            'deal':{
                'error_messages': {
                    'does_not_exist': 'Please enter a valid deal.',
                    'incorrect_type': 'Please enter a valid deal id.',
                }
            },
        }
    def validate(self, attrs):
        lead = attrs.get('lead', getattr(self.instance, 'lead', None))
        contact = attrs.get('contact', getattr(self.instance, 'contact', None))
        company = attrs.get('company', getattr(self.instance, 'company', None))
        deal = attrs.get('deal', getattr(self.instance, 'deal', None))

        if not any([lead, contact, company, deal]):
            raise serializers.ValidationError("A follow-up must be associated with at least one entity (Lead, Contact, Company, or Deal).")
            
        return attrs
        

class NoteSerializer(serializers.ModelSerializer):
    # created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Note
        fields = ['id', 'entity_type', 'object_id', 'content', 'created_by', 'created_at']
        read_only_fields = ['id','created_at','created_by']
        extra_kwargs = {
            'entity_type':{
                'error_messages': {
                    'invalid_choice': f'Invalid Type. Please choose a valid choice.Allowed choices: {EntityType.values}',
                }
            },
            'content':{
                'required':True,
                'allow_null':False,
                'allow_blank':False,
                'error_messages': {
                    'blank': 'Please fill out your content',
                    'null': 'content field must not be null.',
                    'required':"content is required."
                }
            },
        }

    def validate(self, attrs):
        # Determine entity_type and object_id (support both POST create and PATCH update)
        entity_type = attrs.get('entity_type', getattr(self.instance, 'entity_type', None))
        object_id = attrs.get('object_id', getattr(self.instance, 'object_id', None))

        if not entity_type or not object_id:
            raise serializers.ValidationError("Both 'entity_type' and 'object_id' are required.")

        # Entity existence check mapping
        model_mapping = {
            EntityType.LEAD: Lead,
            EntityType.CONTACT: Contact,
            EntityType.COMPANY: Company,
            EntityType.DEAL: Deal,
        }

        target_model = model_mapping.get(entity_type)
        
        if target_model:
            if not target_model.objects.filter(id=object_id).exists():
                raise serializers.ValidationError({
                    'object_id': f"{entity_type.capitalize()} with ID {object_id} does not exist."
                })

        return attrs