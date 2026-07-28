import traceback

from django.db.models import Sum, Count
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from authentication.activities import log_activity
from authentication.models import ActivityAction, ActivityModule
from .models import Deal, DealStage,FollowUp, FollowUpStatus
from .serializers import DealSerializer, FollowUpSerializer


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def deal_view(request, pk=None):
    if request.method == 'GET':
        try:
            if pk:
                deal = Deal.objects.get(pk=pk)#.prefetch_related()
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

            # with transaction.atomic():
            updated_deal = serializer.save()

            # Loop through tracked fields to detect dynamic changes
            changes = []
            for field in tracked_fields:
                old_val = old_values[field]
                new_val = getattr(updated_deal, field)

                if old_val != new_val:
                    field_display = field.replace('_id', '')
                    changes.append(f"{field_display} from '{old_val}' to '{new_val}'")

            # Construct activity log entry
            if changes:
                log_description = f"Updated Deal '{updated_deal.title}': Changed {', '.join(changes)}."
            else:
                log_description = f"Updated Deal '{updated_deal.title}' (no field changes detected)."

                log_activity(
                    user=request.user,
                    module=ActivityModule.DEAL,
                    action=ActivityAction.UPDATE,
                    object_id=updated_deal.id,
                    description=log_description
                )

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


# ----------------------------------------------------------------------
# UPDATE DEAL STAGE (WON / LOST / MOVE PIPELINE STAGE)
# ----------------------------------------------------------------------
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def deal_stage_update_view(request, pk):
    try:
        deal = Deal.objects.get(pk=pk)
        new_stage = request.data.get('stage')

        if not new_stage or new_stage not in DealStage.values:
            return Response({'status': 0, 'message': f'Invalid stage. Allowed: {DealStage.values}'}, status=status.HTTP_400_BAD_REQUEST)

        if not deal.assigned_to== request.user:
            return Response({"success": 0,"message":'Unauthorized Update. You cannot update this Deal.', 'data':{}},status=status.HTTP_403_FORBIDDEN)

        old_stage = deal.stage
        deal.stage = new_stage
        deal.save()

        log_activity(
            user=request.user, module=ActivityModule.DEAL, action=ActivityAction.UPDATE,
            object_id=deal.id, description=f"Changed stage of deal '{deal.title}' from {old_stage} to {new_stage}.",
            changes={'stage': {'from': old_stage, 'to': new_stage}}
        )

        return Response({'status': 1, 'message': f"Deal moved to stage '{new_stage}'.", 'data': DealSerializer(deal).data})
    except Deal.DoesNotExist:
        return Response({'status': 0, 'message': f'Deal with ID {pk} does not exist.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)


# ----------------------------------------------------------------------
# PIPELINE DASHBOARD / STATS
# ----------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def deal_pipeline_view(request):
    """Returns revenue grouped by sales pipeline stages."""
    pipeline_data = Deal.objects.values('stage').annotate(
        total_value=Sum('value'),
        count=Count('id')
    )
    return Response({'status': 1, 'message': 'Pipeline data fetched.', 'data': list(pipeline_data)})


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
        
        followups = FollowUp.objects.all()
        return Response({'status': 1, 'message': 'Success.', 'data': FollowUpSerializer(followups, many=True).data})

    if request.method == 'POST':
        serializer = FollowUpSerializer(data=request.data)
        if serializer.is_valid():
            f = serializer.save(assigned_to=request.user if not request.data.get('assigned_to') else None)
            log_activity(
                user=request.user, module=ActivityModule.FOLLOWUP, action=ActivityAction.CREATE,
                object_id=f.id, description=f"Scheduled follow-up '{f.title}' for {f.scheduled_at}."
            )
            return Response({'status': 1, 'message': 'Follow-up scheduled.', 'data': serializer.data}, status=status.HTTP_201_CREATED)
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response({'status': 0, 'message': 'Validation error.', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    # UPDATE / DELETE
    try:
        f = FollowUp.objects.get(pk=pk)
        if f.assigned_to!=request.user:
            return Response({"status": 0,"message":'Unauthorized Update. You cannot update this deal.', 'data':{}},status=status.HTTP_403_FORBIDDEN)
        

        if request.method in ['PUT', 'PATCH']:
            serializer = FollowUpSerializer(f, data=request.data, partial=(request.method == 'PATCH'))
            if serializer.is_valid():
                f = serializer.save()
                log_activity(
                                user=request.user, module=ActivityModule.FOLLOWUP, action=ActivityAction.UPDATE,
                                object_id=f.id, description=f"follow-up '{f.title}' updated."
                            )
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
        return Response({'status': 0, 'message': 'FollowUp not found.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def followup_status_update_view(request, pk):
    """Quickly update status (COMPLETED, CANCELLED) and add resolution remarks."""
    try:
        f = FollowUp.objects.get(pk=pk)
        new_status = request.data.get('status')
        remarks = request.data.get('remarks')

        if new_status not in FollowUpStatus.values:
            return Response({'status': 0, 'message': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)

        f.status = new_status
        if remarks:
            f.remarks = remarks
        f.save()

        log_activity(
            user=request.user, module=ActivityModule.TASK, action=ActivityAction.UPDATE,
            object_id=f.id, description=f"Marked follow-up '{f.title}' as {new_status}."
        )

        return Response({'status': 1, 'message': f'Follow-up updated to {new_status}.', 'data': FollowUpSerializer(f).data})
    except FollowUp.DoesNotExist:
        return Response({'status': 0, 'message': 'Follow-up not found.', 'data': {}}, status=status.HTTP_404_NOT_FOUND)