import traceback

from django.db.models import Sum, Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.activities import log_activity
from authentication.models import ActivityAction, ActivityModule
from lead.models import Lead
from customer.models import Contact,Company
from .models import Deal, DealStage,FollowUp, FollowUpStatus,Note
from .serializers import DealSerializer, FollowUpSerializer,NoteSerializer

import django_filters
from django.utils import timezone
from django.db.models import Q

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def deal_view(request, pk=None):
    if request.method == 'GET':
        try:
            if pk:
                deal = Deal.objects.get(pk=pk)
                serializer = DealSerializer(deal)
            else:
                deals = Deal.objects.all()
                serializer = DealSerializer(deals, many=True)
            return Response({'status': 1, 'message': 'Data retrieved successfully.', 'data': serializer.data})
        except Deal.DoesNotExist:
            return Response({'status': 0, 'message': f'Deal with ID {pk} does not exist.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        serializer = DealSerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.validated_data.get('contact').company
            deal = serializer.save(assigned_to=request.user,company = company)
            log_activity(
                user=request.user, module=ActivityModule.DEAL, action=ActivityAction.CREATE,
                object_id=deal.id, description=f"Created deal '{deal.title}' (${deal.value})."
            )
            return Response({'status': 1, 'message': 'Deal created successfully.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response({'status': 0, 'message': 'Validation error.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    try:
        deal = Deal.objects.get(pk=pk)

        if deal.assigned_to!=request.user:
            return Response({"status": 0,"message":'Unauthorized Update. You cannot update this deal.', 'data':{}},status=status.HTTP_403_FORBIDDEN)

        # if request.method in ['PUT', 'PATCH']:
        #     serializer = DealSerializer(deal, data=request.data, partial=(request.method == 'PATCH'))
        #     if serializer.is_valid():
        #         deal = serializer.save(assigned_to = request.user)
        #         log_activity(
        #             user=request.user, module=ActivityModule.DEAL, action=ActivityAction.UPDATE,
        #             object_id=deal.id, description=f"Updated deal '{deal.title}'."
        #         )
        #         return Response({'status': 1, 'message': 'Deal updated successfully.', 'data': serializer.data})
        #     return Response({'status': 0, 'message': 'Validation error.', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        if request.method in ['PUT', 'PATCH']:
            # Fields tracked for field-by-field log comparison
            tracked_fields = ['title', 'value', 'stage', 'expected_close_date', 'company_id', 'contact_id', 'assigned_to_id', 'description']
            old_values = {field: getattr(deal, field) for field in tracked_fields}

            serializer = DealSerializer(deal, data=request.data, partial=(request.method == 'PATCH'))
            if not serializer.is_valid():
                errors = {key: err[0] for key, err in serializer.errors.items()}
                return Response({'status': 0, 'message': 'Validation error.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

            updated_deal = serializer.save()

            changes = []
            for field in tracked_fields:
                old_val = old_values[field]
                new_val = getattr(updated_deal, field)

                if old_val != new_val:
                    field_display = field.replace('_id', '')
                    changes.append(f"{field_display} from '{old_val}' to '{new_val}'")

            if changes:
                log_description = f"Updated Deal '{updated_deal.title}': Changed {', '.join(changes)}."
            else:
                log_description = f"Updated Deal '{updated_deal.title}' (no field changes detected)."

                log_activity(user=request.user,module=ActivityModule.DEAL,action=ActivityAction.UPDATE,object_id=updated_deal.id,description=log_description)

            return Response({'status': 1, 'message': 'Deal updated successfully.', 'data': serializer.data}, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            deal_id, title = deal.id, deal.title
            deal.delete()
            log_activity(
                user=request.user, module=ActivityModule.DEAL, action=ActivityAction.DELETE,
                object_id=deal_id, description=f"Deleted deal '{title}' (ID: {deal_id})."
            )
            return Response({'status': 1, 'message': 'Deal deleted successfully.', 'data': {}})

    except Deal.DoesNotExist:
        return Response({'status': 0, 'message': f'Deal with ID {pk} does not exist.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)

from decimal import Decimal
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deal_pipeline_view(request):
    pipeline_summary = []
    
    # Iterate over defined DealStage choices to guarantee all stages are represented
    for stage_code, stage_label in DealStage.choices:
        stage_deals = Deal.objects.filter(stage=stage_code)
        aggregate_data = stage_deals.aggregate(
            total_value=Sum('value'),
            count=Count('id')
        )

        stage_value = aggregate_data['total_value'] if aggregate_data['total_value'] is not None else Decimal('0.00')
        pipeline_summary.append({
            'stage': stage_code,
            'stage_display': stage_label,
            'count': aggregate_data['count'] or 0,
            'total_value': stage_value
        })

    total_pipeline_value = sum(item['total_value'] for item in pipeline_summary)
    total_deals_count = sum(item['count'] for item in pipeline_summary)

    return Response({
        'status': 1,
        'message': 'Deal pipeline metrics fetched successfully.',
        'data': {
            'stages': pipeline_summary,
            'total_deals_count': total_deals_count,
            'total_pipeline_value': total_pipeline_value
        }
    }, status=status.HTTP_200_OK)

class FollowUpFilter(django_filters.FilterSet):
    # 1. Exact entity/module object filters
    lead = django_filters.NumberFilter(field_name='lead__id')
    deal = django_filters.NumberFilter(field_name='deal__id')
    company = django_filters.NumberFilter(field_name='company__id')
    contact = django_filters.NumberFilter(field_name='contact__id')
    assigned_to = django_filters.NumberFilter(field_name='assigned_to__id')

    # 2. Status & Type choices
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    followup_type = django_filters.CharFilter(field_name='followup_type', lookup_expr='iexact')

    # 3. Upcoming vs. History Filters
    # ?timeframe=upcoming or ?timeframe=history
    timeframe = django_filters.CharFilter(method='filter_by_timeframe')

    # 4. Custom Date Range Filters
    scheduled_after = django_filters.DateTimeFilter(field_name='scheduled_at', lookup_expr='gte')
    scheduled_before = django_filters.DateTimeFilter(field_name='scheduled_at', lookup_expr='lte')

    # 5. Search by title, description, or remarks
    search = django_filters.CharFilter(method='filter_by_search')

    class Meta:
        model = FollowUp
        fields = [
            'lead', 'deal', 'company', 'contact', 'assigned_to',
            'status', 'followup_type', 'timeframe',
            'scheduled_after', 'scheduled_before', 'search'
        ]

    def filter_by_timeframe(self, queryset, name, value):
        now = timezone.now()
        val = value.lower().strip()

        if val == 'upcoming':
            # Scheduled in the future AND not yet completed/cancelled
            return queryset.filter(scheduled_at__gte=now).exclude(status__in=[FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED])
        
        elif val in ['history', 'past']:
            # Either already past scheduled date OR marked completed/cancelled
            return queryset.filter(
                Q(scheduled_at__lt=now) | Q(status__in=[FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED])
            )

        return queryset

    def filter_by_search(self, queryset, name, value):
        query = value.strip()
        if not query:
            return queryset

        return queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(remarks__icontains=query)
        )

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def followup_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                followup = FollowUp.objects.get(pk=pk)
                return Response({'status': 1, 'message': 'Followups :', 'data': FollowUpSerializer(followup).data})
            except FollowUp.DoesNotExist:
                return Response({'status': 0, 'message': 'FollowUp not found.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)
        
        # followups = FollowUp.objects.all()
        queryset = FollowUp.objects.all().order_by('scheduled_at')

        followups = FollowUpFilter(request.GET, queryset=queryset).qs
        return Response({'status': 1, 'message': 'Success.', 'data': FollowUpSerializer(followups, many=True).data})

    if request.method == 'POST':
        serializer = FollowUpSerializer(data=request.data)
        if serializer.is_valid():
            deal = serializer.validated_data.get('deal')
            contact = serializer.validated_data.get('contact')
            company = serializer.validated_data.get('company')

            if deal:
                if not contact and deal.contact:
                    contact = deal.contact
                if not company and deal.company:
                    company = deal.company

            if contact and not company:
                if getattr(contact, 'company', None):
                    company = contact.company

            # Save with auto-linked instances and fallback assigned_to to request.user
            f = serializer.save(assigned_to=request.user if not request.data.get('assigned_to') else None,contact=contact,company=company)
            log_activity(
                user=request.user, module=ActivityModule.FOLLOWUP, action=ActivityAction.CREATE,
                object_id=f.id, description=f"Scheduled follow-up '{f.title}' for {f.scheduled_at}."
            )
            return Response({'status': 1, 'message': 'Follow-up scheduled.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response({'status': 0, 'message': 'Validation error.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    try:
        f = FollowUp.objects.get(pk=pk)
        if f.assigned_to!=request.user:
            return Response({"status": 0,"message":'Unauthorized Update. You cannot update this deal.', 'data':{}},status=status.HTTP_403_FORBIDDEN)
        

        if request.method in ['PUT', 'PATCH']:
            serializer = FollowUpSerializer(f, data=request.data, partial=(request.method == 'PATCH'))
            if serializer.is_valid():
                deal = serializer.validated_data.get('deal', f.deal)
                contact = serializer.validated_data.get('contact', f.contact)
                company = serializer.validated_data.get('company', f.company)

                if deal:
                    if not contact and deal.contact:
                        contact = deal.contact
                    if not company and deal.company:
                        company = deal.company

                if contact and not company:
                    if contact.company:
                        company = contact.company

                f = serializer.save(contact=contact, company=company)
                log_activity(user=request.user, module=ActivityModule.FOLLOWUP, action=ActivityAction.UPDATE,object_id=f.id, description=f"follow-up '{f.title}' updated.")
                return Response({'status': 1, 'message': 'Follow-up updated.', 'data': serializer.data})
            
            errors = {key: err[0] for key, err in serializer.errors.items()}
            return Response({'status': 0, 'message': 'Validation error.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            log_activity(
                user=request.user, module=ActivityModule.FOLLOWUP, action=ActivityAction.DELETE,
                object_id=f.id, description=f"follow-up '{f.title}' deleting..."
            )
            f.delete()
            return Response({'status': 1, 'message': 'Follow-up deleted.', 'data': {}})
    except FollowUp.DoesNotExist:
        if pk is None:
            return Response({'status': 0, 'message': 'ID is required for update/delete operations.', 'data': {}}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 0, 'message': 'FollowUp not found.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def note_view(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                note = Note.objects.get(pk=pk)
                return Response({'status': 1,'message': 'Note details fetched successfully.','data': NoteSerializer(note).data}, status=status.HTTP_200_OK)
            except Note.DoesNotExist:
                return Response({'status': 0,'message': 'Note not found.','data': {}}, status=status.HTTP_404_NOT_FOUND)

        queryset = Note.objects.all()
        entity_type = request.query_params.get('entity_type')
        object_id = request.query_params.get('object_id')

        if entity_type:
            queryset = queryset.filter(entity_type__iexact=entity_type)
        if object_id:
            queryset = queryset.filter(object_id=object_id)

        serializer = NoteSerializer(queryset, many=True)
        return Response({'status': 1,'message': 'Notes fetched successfully.','data': serializer.data}, status=status.HTTP_200_OK)

    if request.method == 'POST':
        serializer = NoteSerializer(data=request.data)
        if serializer.is_valid():
            # Save note and explicitly assign the logged-in user as author
            note = serializer.save(created_by=request.user)

            # Log Activity
            log_activity(user=request.user,module="NOTE",
                        action=ActivityAction.CREATE,object_id=note.id,description=f"Added a note on {note.entity_type} ID #{note.object_id}.")

            return Response({'status': 1,'message': 'Note created successfully.','data': NoteSerializer(note).data}, status=status.HTTP_201_CREATED)

        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response({'status': 0,'message': 'Validation error.','errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    if not pk:
        return Response({'status': 0,'message': 'Note ID (pk) is required for UPDATE or DELETE operations.','data': {}}, status=status.HTTP_400_BAD_REQUEST)

    try:
        note = Note.objects.get(pk=pk)

        if note.created_by != request.user:
            return Response({'status': 0,'message': 'Unauthorized Update. You can only modify your own notes.','data': {}}, status=status.HTTP_403_FORBIDDEN)

        if request.method in ['PUT', 'PATCH']:
            serializer = NoteSerializer(note,data=request.data,partial=(request.method == 'PATCH'))
            if serializer.is_valid():
                note = serializer.save()

                log_activity(user=request.user,module="NOTE",action=ActivityAction.UPDATE,object_id=note.id,
                            description=f"Updated note ID #{note.id} on {note.entity_type} ID #{note.object_id}.")
                return Response({'status': 1,'message': 'Note updated successfully.','data': serializer.data}, status=status.HTTP_200_OK)

            errors = {key: err[0] for key, err in serializer.errors.items()}
            return Response({'status': 0,'message': 'Validation error.','errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            log_activity(user=request.user,module="NOTE",
                        action=ActivityAction.DELETE,object_id=note.id,description=f"Deleted note ID #{note.id} from {note.entity_type} ID #{note.object_id}.")
            note.delete()
            return Response({'status': 1,'message': 'Note deleted successfully.','data': {}}, status=status.HTTP_200_OK)

    except Note.DoesNotExist:
        return Response({'status': 0,'message': 'Note not found.','data': {}}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary_view(request):
    """
    GET: Returns summary metrics for Customers, Leads, Deals, Sales, and Conversion Rate.
    """
    total_leads = Lead.objects.count()
    converted_leads = Lead.objects.filter(is_converted=True).count()
    conversion_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0.0

    deal_metrics = Deal.objects.aggregate(
          total_value=Sum('value'),
        won_value=Sum('value', filter=Q(stage=DealStage.CLOSED_WON)),
        lost_value=Sum('value', filter=Q(stage=DealStage.CLOSED_LOST)),
        total_deals=Count('id'),
        won_deals=Count('id', filter=Q(stage=DealStage.CLOSED_WON)),
        lost_deals=Count('id', filter=Q(stage=DealStage.CLOSED_LOST))
    )

    return Response({
        'status': 1,
        'message': 'Dashboard metrics retrieved successfully.',
        'data': {
            'customers': {
                'total_companies': Company.objects.count(),
                'total_contacts': Contact.objects.count(),
            },
            'leads': {
                'total_leads': total_leads,
                'converted_leads': converted_leads,
                'conversion_rate_percentage': conversion_rate,
            },
            'deals': {
                'total_deals': deal_metrics['total_deals'] or 0,
                'won_deals': deal_metrics['won_deals'] or 0,
                'lost_deals': deal_metrics['lost_deals'] or 0,
                'total_pipeline_value': deal_metrics['total_value'] or 0.00,
                'total_won_value': deal_metrics['won_value'] or 0.00,
            }
        }
    })