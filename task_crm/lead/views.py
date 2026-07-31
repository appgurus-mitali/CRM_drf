from .models import Lead,LeadStatus
from .serializers import LeadSerializer
from authentication.models import MyUser,ActivityModule,ActivityAction
from customer.models import Company,Contact
from sales.serializers import DealSerializer

from authentication.activities import log_activity

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

import traceback

from django.db import transaction
from django.db.models import Q

import django_filters

from rest_framework.settings import api_settings

# Create your views here.
class LeadFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    priority = django_filters.CharFilter(field_name='priority', lookup_expr='iexact')
    source = django_filters.CharFilter(field_name='source', lookup_expr='iexact')
    assigned_lead = django_filters.NumberFilter(field_name='assigned_lead__id')

    search = django_filters.CharFilter(method='filter_by_search')

    class Meta:
        model = Lead
        fields = ['status', 'priority', 'source', 'assigned_lead', 'search']

    def filter_by_search(self, queryset, name, value):
        query = value.strip()
        if not query:
            return queryset

        return queryset.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(company_name__icontains=query)
        )


@api_view(['GET','POST','PUT','PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def lead_view(request,pk=None):
    if request.method=='GET':
        try:
            if pk is not None:
                user = Lead.objects.get(id=pk)
                serializer = LeadSerializer(user)
            else : 
                # users = Lead.objects.all()
                # serializer = LeadSerializer(users,many=True)

                queryset = LeadFilter(request.GET, queryset=Lead.objects.all()).qs
                paginator = api_settings.DEFAULT_PAGINATION_CLASS()
                page = paginator.paginate_queryset(queryset, request)
                serializer = LeadSerializer(page, many=True)

            return Response({'status':1,'message':f'Welcome {request.user.username}','data':serializer.data},status=status.HTTP_200_OK)
        except (Lead.DoesNotExist,Lead.MultipleObjectsReturned):
                    return Response({'status':0,'message':f'User not exists.','data':{}},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
        return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method=='POST':
        try:
            serializer = LeadSerializer(data=request.data)
            if serializer.is_valid():
                lead = serializer.save()
                log_activity(user=None,module=ActivityModule.LEAD,action=ActivityAction.CREATE,object_id=lead.id,description=f"Created new lead '{lead.first_name} {lead.last_name}'.")
                return Response({'status':1,'message':f'Lead Created Successfully','data':serializer.data},status=status.HTTP_201_CREATED)
            errors={key:err[0] for key,err in serializer.errors.items()}
            return Response({'status':0,'message':'Validation failed.','error':errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
            return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        lead = Lead.objects.get(pk=pk)
        # print(lead.assigned_lead,lead.assigned_lead!=request.user)

        if lead.assigned_lead is not None and lead.assigned_lead!=request.user:
            return Response({"status": 0,"message":'Unauthorized Update. You cannot update this lead.', 'data':{}},status=status.HTTP_403_FORBIDDEN)

        if request.method in ['PUT', 'PATCH']:
                partial = (request.method == 'PATCH')
                serializer = LeadSerializer(lead, data=request.data, partial=partial)
                if serializer.is_valid():
                    updated_lead = serializer.save()
                    log_activity(user=request.user,module=ActivityModule.LEAD,action=ActivityAction.UPDATE,object_id=updated_lead.id,description=f"Updated details for lead '{updated_lead.first_name} {updated_lead.last_name}'.")
                    return Response({'status':1,'message':f'Lead Updated Successfully','data':serializer.data},status=status.HTTP_200_OK)
                errors={key:err[0] for key,err in serializer.errors.items()}
                return Response({'status':0,'message':'Validation failed.','error':errors},status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            print('in delete lead')
            log_activity(user=request.user,module=ActivityModule.LEAD,action=ActivityAction.DELETE,object_id=lead.id,description=f"Deleted lead '{lead.first_name}'.")
            lead.delete()
            return Response({"status": 0,"message": "Lead deleted successfully.","data": {}}, status=status.HTTP_200_OK)
    except Lead.DoesNotExist:
        return Response({"status": 0,"message": f"Lead with ID {pk} does not exist.","data": {}},status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
            return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['POST'])
# def create_leadview(request):
#     try:
#         serializer = LeadSerializer(data=request.data)
#         if serializer.is_valid():
#             lead = serializer.save()
#             log_activity(user=None,module=ActivityModule.LEAD,action=ActivityAction.CREATE,object_id=lead.id,description=f"Created new lead '{lead.first_name} {lead.last_name}'.")
#             return Response({'status':1,'message':f'Lead Created Successfully','data':serializer.data},status=status.HTTP_201_CREATED)
#         errors={key:err[0] for key,err in serializer.errors.items()}
#         return Response({'status':0,'message':'Validation failed.','error':errors},status=status.HTTP_400_BAD_REQUEST)
#     except Exception as e:
#         print("\n\nException in reg")
#         traceback.print_exc()
#         return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def lead_assign_view(request,pk):
    try:
        lead = Lead.objects.get(id=pk)
        user_id = request.data.get('user_id')

        if user_id is None or user_id=='':
            return Response({"status": 0,"message": "Invalid data.",'errors':{'user_id':"user_id is required."}}, status=status.HTTP_400_BAD_REQUEST)
        if not MyUser.objects.filter(id=user_id).exists():
            return Response({"status": 0,"message": "User does not exist.",'data':{}}, status=status.HTTP_404_NOT_FOUND)
        if lead.assigned_lead is not None:
            return Response({"status": 0,"message": f"Already assinged lead to {lead.assigned_lead}",'data':{}}, status=status.HTTP_400_BAD_REQUEST)

        lead.assigned_lead_id = user_id
        lead.save()
        log_activity(user=request.user,module=ActivityModule.LEAD,action=ActivityAction.UPDATE,object_id=lead.id,description=f"Assigned lead '{lead.first_name} {lead.last_name}' to user id'{user_id}'.")
        return Response({"status": 1,"message": f"Lead assigned to user ID {user_id} successfully.",'data':{}}, status=status.HTTP_200_OK)
    except Lead.DoesNotExist:
            return Response({"status": 0,"message": f"Lead with ID {pk} does not exist.","data": {}},status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
            print("\n\nException in reg")
            traceback.print_exc()
            return Response({"status": 0,'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.','data':{}},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def lead_convert_view(request,pk):
    try:
        lead = Lead.objects.get(id=pk)
        if lead.assigned_lead!=request.user:
            return Response({"status": 0,"message":'Unauthorized Update. You cannot update this lead.', 'data':{}},status=status.HTTP_403_FORBIDDEN)

        if lead.is_converted:
            return Response({"status": 0,"message":'Already converted.', 'data':{}},status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            company_instance = None

            if lead.company_name and lead.company_name.strip():
                company_name = lead.company_name.strip()
                company_instance, company_created = Company.objects.get_or_create(name__iexact=company_name,
                                                                                defaults={'name': company_name,'assigned_to': lead.assigned_lead})

                # company_instance = Company.objects.filter(name__iexact=company_name_clean).first()
                # if not company_instance:
                #     company_instance = Company.objects.create(
                #         name=company_name_clean,
                #         assigned_to=lead.assigned_lead
                #     )

                log_activity(user=request.user,module=ActivityModule.COMPANY,action=ActivityAction.CREATE,object_id=company_instance.id,
                                        description=f"Auto-created Company {company_instance.name} from lead conversion' ")

            contact, created = Contact.objects.get_or_create(
                email__iexact=lead.email.strip(),
                phone = lead.phone,
                defaults={
                    'first_name': lead.first_name,
                    'last_name': lead.last_name,
                    'email':lead.email,
                    'phone': lead.phone,
                    'company': company_instance,
                    'source': lead.source,
                    'converted_from_lead': lead,
                    'assigned_to': lead.assigned_lead,
                }
            )

            if not created:
                if company_instance:
                    contact.company = company_instance
                    contact.job_title = None
                    contact.department =None
                contact.converted_from_lead = lead
                contact.save()

            lead.is_converted = True
            lead.status = LeadStatus.QUALIFIED
            lead.save()
            log_activity(user=request.user,module=ActivityModule.LEAD,action=ActivityAction.CONVERT,object_id=lead.id,
                        description=f"Converted lead '{lead.first_name} {lead.last_name}' into Contact (ID: {contact.id}).")

            response_data = {
                'lead_id': lead.id,
                'contact_id': contact.id,
                'company_id': company_instance.id if company_instance else None
            }
            message = f"Lead '{lead.first_name} {lead.last_name}' converted successfully!"

            is_deal = request.data.get("deal",None)
            if is_deal is not None:
                deal_data = request.data
                deal_data['contact'] = contact.id
                serializer = DealSerializer(data=request.data)
                if serializer.is_valid():
                    deal = serializer.save(
                        assigned_to=lead.assigned_lead,
                        company=company_instance,
                        contact=contact
                    )
                    response_data['deal_id']=deal.id

                    log_activity(
                        user=request.user,
                        module=ActivityModule.DEAL,
                        action=ActivityAction.CREATE,
                        object_id=deal.id,
                        description=f"Auto-created Deal '{deal.title}' during lead conversion."
                    )
                else:
                    deal_errors = {key: err[0] for key, err in serializer.errors.items()}
                    deal_warning = {
                        'message': 'Deal auto-creation failed validation. Please create the deal manually using the deals endpoint.',
                        'errors': deal_errors
                    }
                    return Response({'status': 1, 'message': message, 'data': response_data,'deal_warning':deal_warning},status=status.HTTP_200_OK)
            return Response({'status': 1, 'message': message, 'data': response_data},status=status.HTTP_200_OK)
        return Response({"status": 0,"message": f"Lead conversion failed!","data": {}},status=status.HTTP_200_OK)
    except Lead.DoesNotExist:
        return Response({"status": 0,"message": f"Lead with ID {pk} does not exist.","data": {}},status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print("\n\nException in reg")
        traceback.print_exc()
        return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.',"data": {}},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
