from django.db import models

# Create your models here.

class LeadStatus(models.TextChoices):
    NEW = 'NEW', 'New'
    CONTACTED = 'CONTACTED', 'Contacted'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    QUALIFIED = 'QUALIFIED', 'Qualified'        # Ready to convert
    UNQUALIFIED = 'UNQUALIFIED', 'Unqualified'  # Spam or no budget
    CONVERTED = 'CONVERTED', 'Converted'        # Already converted

class DealStage(models.TextChoices):
    QUALIFICATION = 'QUALIFICATION', 'Qualification'
    PROPOSAL_SENT = 'PROPOSAL_SENT', 'Proposal Sent'
    NEGOTIATION = 'NEGOTIATION', 'Negotiation'
    CLOSED_WON = 'CLOSED_WON', 'Closed Won'
    CLOSED_LOST = 'CLOSED_LOST', 'Closed Lost'
    

class LeadSource(models.TextChoices):
    WEBSITE = 'WEBSITE', 'Website'
    REFERRAL = 'REFERRAL', 'Referral'
    SOCIAL_MEDIA = 'SOCIAL_MEDIA', 'Social Media'
    EMAIL_CAMPAIGN = 'EMAIL_CAMPAIGN', 'Email Campaign'
    FACEBOOK = 'FACEBOOK', 'Facebook'
    INSTAGRAM = 'INSTAGRAM', 'Instagram'
    LINKEDIN = 'LINKEDIN', 'LinkedIn'
    COLD_CALLING = 'COLD_CALLING', 'Cold Calling'
    WALK_IN = 'WALK_IN', 'Walk-in'


class Priority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'


class Lead(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.BigIntegerField()

    company_name = models.CharField(max_length=300,null=True,blank=True)

    description = models.TextField(blank=True, null=True)
    assigned_lead = models.ForeignKey("authentication.MyUser", related_name='leads', on_delete=models.SET_NULL ,null=True,blank=True) 
    
    # Task Required Fields
    status = models.CharField(max_length=30, choices=LeadStatus.choices, default=LeadStatus.NEW)
    source = models.CharField(max_length=30, choices=LeadSource.choices, default=LeadSource.WEBSITE)
    priority = models.CharField(max_length=30,choices=Priority.choices,default=Priority.LOW)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_converted = models.BooleanField(default=False)
    def __str__(self):
        return f"Lead: {self.first_name} {self.last_name} ({self.status})"