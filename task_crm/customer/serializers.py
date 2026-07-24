from rest_framework import serializers
from .models import Company, Contact

class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer for Company Model.
    Handles listing, creating, and updating companies.
    """
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'domain',
            'industry',
            'website',
            'address',
            'city',
            'state',
            'country',
            'zip_code',
            'annual_revenue',
            'assigned_to',
            'created_at',
            'updated_at',
        ]
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
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone',
            'mobile',
            'job_title',
            'department',
            'company',          # Write-only ID for POST/PUT (e.g. 5)
            'company_detail',   # Read-only nested dict for GET responses
            'source',
            'converted_from_lead',
            'assigned_to',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """
        Ensure email uniqueness on updates and creations.
        """
        instance = getattr(self, 'instance', None)
        query = Contact.objects.filter(email__iexact=value)
        if instance:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError("A contact with this email address already exists.")
        return value