from .models import Company,Contact
from .serializers import CompanySerializer,ContactSerializer

from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAdminUser,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

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
                serializer.save()
                return Response(
                    {'status': 1, 'message': 'Company created successfully.', 'data': serializer.data},
                    status=status.HTTP_201_CREATED
                )
            errors = {key: err[0] for key, err in serializer.errors.items()}
            return Response(
                {'status': 0, 'message': 'Validation failed.', 'error': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            traceback.print_exc()
            return Response(
                {'status': 0, 'message': 'An Internal Server Error Occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
    except Company.DoesNotExist:
        return Response(
            {'status': 0, 'message': f'Company with ID {pk} does not exist.', 'data': {}},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = CompanySerializer(company)
        return Response(
            {'status': 1, 'message': 'Company retrieved successfully.', 'data': serializer.data},
            status=status.HTTP_200_OK
        )

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = CompanySerializer(company, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'status': 1, 'message': 'Company updated successfully.', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response(
            {'status': 0, 'message': 'Validation failed.', 'error': errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        company.delete()
        return Response(
            {'status': 1, 'message': 'Company deleted successfully.', 'data': {}},
            status=status.HTTP_200_OK
        )

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contact_list_create_view(request):
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
            #     )

            serializer = ContactSerializer(contacts, many=True)
            return Response(
                {'status': 1, 'message': 'Contacts retrieved successfully.', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception:
            traceback.print_exc()
            return Response(
                {'status': 0, 'message': 'An Internal Server Error Occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif request.method == 'POST':
        try:
            serializer = ContactSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(assigned_to=request.user)
                return Response(
                    {'status': 1, 'message': 'Contact created successfully.', 'data': serializer.data},
                    status=status.HTTP_201_CREATED
                )
            errors = {key: err[0] for key, err in serializer.errors.items()}
            return Response(
                {'status': 0, 'message': 'Validation failed.', 'error': errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            traceback.print_exc()
            return Response(
                {'status': 0, 'message': 'An Internal Server Error Occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
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
    except Contact.DoesNotExist:
        return Response(
            {'status': 0, 'message': f'Contact with ID {pk} does not exist.', 'data': {}},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = ContactSerializer(contact)
        return Response(
            {'status': 1, 'message': 'Contact retrieved successfully.', 'data': serializer.data},
            status=status.HTTP_200_OK
        )

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = ContactSerializer(contact, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'status': 1, 'message': 'Contact updated successfully.', 'data': serializer.data},
                status=status.HTTP_200_OK
            )
        errors = {key: err[0] for key, err in serializer.errors.items()}
        return Response(
            {'status': 0, 'message': 'Validation failed.', 'error': errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == 'DELETE':
        contact.delete()
        return Response(
            {'status': 1, 'message': 'Contact deleted successfully.', 'data': {}},
            status=status.HTTP_200_OK
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_company_contact_view(request, company_id):
    """Directly attach a secondary stakeholder/colleague to an existing Company."""
    try:
        company = Company.objects.get(pk=company_id)
    except Company.DoesNotExist:
        return Response(
            {'status': 0, 'message': f'Company with ID {company_id} does not exist.', 'data': {}},
            status=status.HTTP_404_NOT_FOUND
        )

    data = request.data
    # data['company'] = company.id
    # data['assigned_to'] = request.user

    job_title = request.data.get('job_title',None)
    if job_title is None or job_title=="":
        errors['job_title']="Job Title is required."
    department = request.data.get('job_title',None)
    if department is None or department=="":
            errors['department']="Department is required."

    serializer = ContactSerializer(data=data)
    if serializer.is_valid():
        serializer.save(company=company,assigned_to = company.assigned_to.user,job_title=job_title,)
        return Response(
            {'status': 1, 'message': f'Contact added to company "{company.name}" successfully.', 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

    errors = {key: err[0] for key, err in serializer.errors.items()}
    return Response(
        {'status': 0, 'message': 'Validation failed.', 'error': errors},
        status=status.HTTP_400_BAD_REQUEST
    )