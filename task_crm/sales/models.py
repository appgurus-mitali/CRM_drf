from django.db import models
from customer.models import Company,Contact
from authentication.models import MyUser
from lead.models import Lead

class DealStage(models.TextChoices):
    PROSPECTING = 'PROSPECTING', 'Prospecting'
    QUALIFICATION = 'QUALIFICATION', 'Qualification'
    PROPOSAL = 'PROPOSAL', 'Proposal Sent'
    NEGOTIATION = 'NEGOTIATION', 'In Negotiation'
    CLOSED_WON = 'CLOSED_WON', 'Closed Won'
    CLOSED_LOST = 'CLOSED_LOST', 'Closed Lost'

# Create your models here.
class Deal(models.Model):
    title = models.CharField(max_length=200)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    stage = models.CharField(max_length=20, choices=DealStage.choices, default=DealStage.PROSPECTING)
    expected_close_date = models.DateField(null=True, blank=True)

    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')
    assigned_to = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='deals')

    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} (${self.value}) - {self.get_stage_display()}"

class FollowUpType(models.TextChoices):
    CALL = 'CALL', 'Phone Call'
    MEETING = 'MEETING', 'Meeting'
    EMAIL = 'EMAIL', 'Email'
    TASK = 'TASK', 'General Task'


class FollowUpStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class FollowUp(models.Model):
    title = models.CharField(max_length=200)
    followup_type = models.CharField(max_length=20, choices=FollowUpType.choices, default=FollowUpType.CALL)
    status = models.CharField(max_length=20, choices=FollowUpStatus.choices, default=FollowUpStatus.PENDING)

    scheduled_at = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='followups')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True, related_name='followups')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='followups')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='followups')
    assigned_to = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='followups')

    remarks = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.get_followup_type_display()}: {self.title} @ {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"

class EntityType(models.TextChoices):
    LEAD = 'LEAD', 'Lead'
    CONTACT = 'CONTACT', 'Contact'
    COMPANY = 'COMPANY', 'Company'
    DEAL = 'DEAL', 'Deal'

class Note(models.Model):
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    object_id = models.PositiveIntegerField()
    
    content = models.TextField()
    created_by = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='notes')
    created_at = models.DateTimeField(auto_now_add=True)