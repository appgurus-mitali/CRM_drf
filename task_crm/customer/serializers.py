from rest_framework import serializers
from .models import Company, Contact,ContactSource

from django.db.models import Q

class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer for Company Model.
    Handles listing, creating, and updating companies.
    """
    class Meta:
        model = Company
        fields = ['id','name','domain','industry','website','address','city','state','country','zip_code','annual_revenue','assigned_to','created_at','updated_at',]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        """Ensure company names are unique (case-insensitive check on updates/creates)."""

        instance = getattr(self, 'instance', None)
        query = Company.objects.filter(name__iexact=value)
        if instance:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact Model.Supports receiving 'company' ID on write (POST/PUT/PATCH),while returning nested 'company_detail' on read (GET)."""

    company_detail = CompanySerializer(source='company', read_only=True)

    class Meta:
        model = Contact
        fields = ['id','first_name','last_name','email','phone','job_title','department','company',
                'source','converted_from_lead','assigned_to','created_at','updated_at',]
        read_only_fields = ['id', 'created_at', 'updated_at','company','job_title','department','converted_from_lead','assigned_to']
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
                    'invalid_choice': f'Invalid Source. Please choose a valid choice.Allowed choices: {ContactSource.values}',
                },
            },
        }


    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')

        existing = Contact.objects.filter(Q(email=email) | Q(phone=phone))

        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)

        errors = {}
        for user in existing:
            if user.email == email:
                errors['email'] = "This email is already registered."
            if user.phone == phone:
                errors['mobile'] = "This mobile number is already in use."

        # company = attrs.get('company')
        # if company is None and self.instance:
        #     company = self.instance.company

        # # 2. Conditional check: If company is provided, check all related fields simultaneously
        # if company:
        #     job_title = attrs.get('job_title')
        #     department = attrs.get('department')

        #     # Check Job Title
        #     if not job_title or not str(job_title).strip():
        #         errors['job_title'] = 'Job title is required when a company is selected.'

        #     # Check Department
        #     if not department or not str(department).strip():
        #         errors['department'] = 'Department is required when a company is selected.'

        if errors:
            raise serializers.ValidationError(errors)
        return attrs