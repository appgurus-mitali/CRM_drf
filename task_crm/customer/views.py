from .models import Company,Contact
from .serializers import CompanySerializer,ContactSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from authentication.activities import log_activity
from authentication.models import ActivityAction,ActivityModule
import traceback

# Create your views here.
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def company_list_create_view(request):
    if request.method=='GET':
        try:
            companies = Company.objects.all()
            serializer = CompanySerializer(companies,many=True)
            return Response({'status':1,'message':"Here's Your Copmpany list.",'data':serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            traceback.print_exc()
            return Response({'status':0,'message':'An Internal Server Error Occurred. Pls check terminal.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    if request.method=='POST':
        try:
            serializer = CompanySerializer(data=request.data)
            if serializer.is_valid():
                company = serializer.save(assigned_to = request.user)
                log_activity(user=request.user, module=ActivityModule.COMPANY, action=ActivityAction.CREATE, object_id=company.id, description=f"Created company '{company.name}'.")

                return Response({'status': 1, 'message': 'Company created successfully.', 'data': serializer.data},status=status.HTTP_201_CREATED)
            errors = {key: err[0] for key, err in serializer.errors.items()}
            return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            traceback.print_exc()
            return Response({'status': 0, 'message': 'An Internal Server Error Occurred.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def company_detail_view(request, pk):
    """
    GET: Retrieve single company.
    PUT/PATCH: Update company details.
    DELETE: Delete company.
    """

    try:
        company = Company.objects.get(pk=pk)
        if company.assigned_to!=request.user:
            return Response({'status': 0, "message":'Unauthorized Update. You cannot update this company.', 'data':{}},status=status.HTTP_403_FORBIDDEN)
    except Company.DoesNotExist:
        return Response({'status': 0, 'message': f'Company with ID {pk} does not exist.', 'data': {}},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CompanySerializer(company)
        return Response({'status': 1, 'message': 'Company retrieved successfully.', 'data': serializer.data},status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = CompanySerializer(company, data=request.data, partial=partial)
        if serializer.is_valid():
            company = serializer.save()
            log_activity(user=request.user, module=ActivityModule.COMPANY, action=ActivityAction.UPDATE, object_id=company.id, description=f"Updated company '{company.name}'")
            return Response({'status': 1, 'message': 'Company updated successfully.', 'data': serializer.data},status=status.HTTP_200_OK)
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        log_activity(user=request.user, module=ActivityModule.COMPANY, action=ActivityAction.DELETE, object_id=company.id, description=f"Deleted company '{company.name}'")
        company.delete()
        return Response({'status': 1, 'message': 'Company deleted successfully.', 'data': {}},status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contact_list_create_view(request,company_id=None):
    """
    GET: List all contacts (supports ?search= query).
    POST: Create a direct contact.
    """
    if request.method == 'GET':
        try:
            # search_query = request.query_params.get('search', '').strip()
            contacts = Contact.objects.all()

            # if search_query:
            #     contacts = contacts.filter(
            #         Q(first_name__icontains=search_query) |
            #         Q(last_name__icontains=search_query) |
            #         Q(email__icontains=search_query) |
            #         Q(company__name__icontains=search_query)
            # )

            serializer = ContactSerializer(contacts, many=True)
            return Response({'status': 1, 'message': 'Contacts retrieved successfully.', 'data': serializer.data},status=status.HTTP_200_OK)
        except Exception:
            traceback.print_exc()
            return Response({'status': 0, 'message': 'An Internal Server Error Occurred.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            data = request.data
            company_id = company_id or data.get('company_id',None)
            company = None
            job_title = None
            department = None
            assigned_to = request.user
            errors = {}
            if company_id is not None:
                company = Company.objects.get(pk=company_id)
                job_title = data.get('job_title')
                department = data.get('department')
                assigned_to = company.assigned_to

                print(job_title,department,company)

                if not job_title or not str(job_title).strip():
                    errors['job_title'] = "Job Title is required."
                if not department or not str(department).strip():
                    errors['department'] = "Department is required."

                if errors:
                    return Response({'status': 0, 'message': 'Validation failed.', 'errors': errors},status=status.HTTP_400_BAD_REQUEST)

            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                contact = serializer.save(company=company,assigned_to = assigned_to,job_title=job_title,department = department)
                log_activity(user=request.user,module=ActivityModule.CONTACT,action=ActivityAction.CREATE,object_id=contact.id,
                            description=f"Created contact '{contact.first_name} {contact.last_name}'" + 
                            (f" for company '{company.name}'." if company else "."))
                return Response({'status': 1, 'message': 'Contact created successfully.', 'data': serializer.data},status=status.HTTP_201_CREATED)
            
            errors = {key: err[0] for key, err in serializer.errors.items()}
            return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)
        except Company.DoesNotExist:
            return Response({'status': 0, 'message': f'Company with ID {company_id} does not exist.', 'data': {}},status=status.HTTP_404_NOT_FOUND)
        except Exception:
            traceback.print_exc()
            return Response({'status': 0, 'message': 'An Internal Server Error Occurred.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def contact_detail_view(request, pk):
    """
    GET: Retrieve single contact.
    PUT/PATCH: Update contact details.
    DELETE: Delete contact.
    """
    try:
        contact = Contact.objects.get(pk=pk)

        if contact.assigned_to!=request.user:
            return Response({'status': 0, "message":'Unauthorized Update. You cannot update this contact.', 'data':{}},status=status.HTTP_403_FORBIDDEN)
    except Contact.DoesNotExist:
        return Response({'status': 0, 'message': f'Contact with ID {pk} does not exist.', 'data': {}},status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ContactSerializer(contact)
        return Response({'status': 1, 'message': 'Contact retrieved successfully.', 'data': serializer.data},status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = ContactSerializer(contact, data=request.data, partial=partial)
        if serializer.is_valid():
            contact = serializer.save()
            log_activity(user=request.user, module=ActivityModule.CONTACT, action=ActivityAction.UPDATE, object_id=contact.id, description=f"Updated contact '{contact.first_name} {contact.last_name}'")
            return Response({'status': 1, 'message': 'Contact updated successfully.', 'data': serializer.data},status=status.HTTP_200_OK)
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        log_activity(user=request.user, module=ActivityModule.CONTACT, action=ActivityAction.DELETE, object_id=contact.id, description=f"Deleted contact '{contact.first_name} {contact.last_name}'")
        contact.delete()
        return Response({'status': 1, 'message': 'Contact deleted successfully.', 'data': {}},status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_company_contact_view(request, company_id):
    """Directly attach a secondary stakeholder/colleague to an existing Company."""
    try:
        company = Company.objects.get(pk=company_id)
    except Company.DoesNotExist:
        return Response({'status': 0, 'message': f'Company with ID {company_id} does not exist.', 'data': {}},status=status.HTTP_404_NOT_FOUND)

    data = request.data
    # data['company'] = company.id
    # data['assigned_to'] = request.user

    errors = {}
    job_title = request.data.get('job_title',None)
    if job_title is None or job_title=="":
        errors['job_title']="Job Title is required."
    department = request.data.get('department',None)
    if department is None or department=="":
            errors['department']="Department is required."

    if errors:
        return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)

    
    serializer = ContactSerializer(data=data)
    if serializer.is_valid():
        contact = serializer.save(company=company,assigned_to = company.assigned_to.user,job_title=job_title,department = department)
        log_activity(user=request.user, module=ActivityModule.CONTACT, action=ActivityAction.CREATE, object_id=contact.id, description=f"Added contact '{contact.first_name} {contact.last_name}' to company '{company.name}'")
        return Response({'status': 1, 'message': f'Contact added to company "{company.name}" successfully.', 'data': serializer.data},status=status.HTTP_201_CREATED)
    errors = {key: err[0] for key, err in serializer.errors.items()}
    return Response({'status': 0, 'message': 'Validation failed.', 'error': errors},status=status.HTTP_400_BAD_REQUEST)