from django.db import models
from authentication.models import MyUser

# Create your models here.
class ContactSource(models.TextChoices):

    REFERRAL = 'REFERRAL', 'Referral'
    EMAIL_CAMPAIGN = 'EMAIL_CAMPAIGN', 'Email Campaign'
    COLD_CALLING = 'COLD_CALLING', 'Cold Calling'
    WALK_IN = 'WALK_IN', 'Walk-in'

class Company(models.Model):
    name = models.CharField(max_length=200, unique=True,null=False,blank=False)
    domain = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)  
    company_detail = models.TextField(blank=True, null=True)
    website = models.URLField(max_length=250, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,help_text="Estimated annual revenue of the client company")
    assigned_to = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='companies')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
    
class Contact(models.Model):
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts'
    )
    job_title = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True,unique=True)

    source = models.CharField(max_length=30, choices=ContactSource.choices, default=ContactSource.REFERRAL)
    converted_from_lead = models.ForeignKey(
        'lead.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_contacts'
    )

    assigned_to = models.ForeignKey(
        MyUser,
        on_delete=models.SET_NULL,
        # null=True,
        # blank=True,
        related_name='contacts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.company:
            return f"{self.first_name} {self.last_name} ({self.company.name})"
        return f"{self.first_name} {self.last_name} (Direct Customer)"

    class Meta:
        ordering = ['-created_at']