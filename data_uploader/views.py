import os
import pandas as pd
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from scraper.models import DODDrugData
from .serializers import DODUploadedFileSerializer
from .data_insertion import insert_dod_data
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .task import insert_dod_drug_data_async, insert_foia_drug_data_async, insert_foia_monthly_status_task, insert_foia_monthly_status_async_task
from rest_framework import generics
from scraper.models import FSSDrug,FOIAUniqueNDCData, FSSVendor
from .serializers import *
from rest_framework.permissions import IsAuthenticated

import csv
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from .models import FOIAMonthlyStats


class UploadDataDODFileView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = DODUploadedFileSerializer

    REQUIRED_COLUMNS = {'ndc_code', 'description', 'price', 'quantity'}
    
    def validate_excel_file(self, file):
        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as e:
            return False, f"Error reading the Excel file: {str(e)}"
        
        if not self.REQUIRED_COLUMNS.issubset(df.columns):
            missing_columns = self.REQUIRED_COLUMNS - set(df.columns)
            return False, f"Missing columns: {', '.join(missing_columns)}"
        
        return True, df
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('dod_file', openapi.IN_FORM, type=openapi.TYPE_FILE, description='Upload file')
    ])

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            dod_file = request.FILES['dod_file']

            # Check file format
            if not dod_file.name.endswith('.xlsx'):
                return Response(
                    {
                        "success": False,
                        "message": "The uploaded file must be an Excel file with .xlsx extension.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate the Excel file
            is_valid, validation_response = self.validate_excel_file(dod_file)
            if not is_valid:
                return Response(
                    {
                        "success": False,
                        "message": validation_response,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Save the file
                file_path = os.path.join('uploads', dod_file.name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb+') as destination:
                    for chunk in dod_file.chunks():
                        destination.write(chunk)

                # Trigger the Celery task
                insert_dod_data.delay(file_path)

                return Response(
                    {
                        "success": True,
                        "message": "File uploaded and processing started",
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            except Exception as e:
                return Response(
                    {
                        "success": False,
                        "message": f"Error saving the file: {str(e)}",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {
                "success": False,
                "message": "Invalid data",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST
        )



class UploadDataFOIAFileView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = DODUploadedFileSerializer
    
    REQUIRED_COLUMNS = [
        'McKesson Station Number', 'NDC', 'Drug Description', 
        'Quantity Purchased', 'Publishable Dollars Spent'
    ]
    
    def validate_txt_file(self, file):
        try:
            df = pd.read_csv(file, delimiter='\t')
        except Exception as e:
            return False, f"Error reading the TXT file: {str(e)}"
        
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            return False, f"Missing columns: {', '.join(missing_columns)}"
        
        return True, df

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('dod_file', openapi.IN_FORM, type=openapi.TYPE_FILE, description='Upload file')
    ])
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            dod_file = request.FILES['dod_file']

            # Check file format
            if not dod_file.name.endswith('.txt'):
                return Response(
                    {
                        "success": False,
                        "message": "The uploaded file must be a text file with .txt extension.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate the TXT file
            is_valid, validation_response = self.validate_txt_file(dod_file)
            if not is_valid:
                return Response(
                    {
                        "success": False,
                        "message": validation_response,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                # Save the file
                file_path = os.path.join('uploads', dod_file.name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb+') as destination:
                    for chunk in dod_file.chunks():
                        destination.write(chunk)

                # Trigger the Celery task
                insert_foia_drug_data_async.delay(file_path)

                return Response(
                    {
                        "success": True,
                        "message": "File uploaded and processing started",
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            except Exception as e:
                return Response(
                    {
                        "success": False,
                        "message": f"Error saving the file: {str(e)}",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(
            {
                "success": False,
                "message": "Invalid data",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        


class FSSDrugUpdateView(generics.UpdateAPIView):
    queryset = FSSDrug.objects.all()
    serializer_class = FSSDrugUpdateSerializer
    permission_classes = [IsAuthenticated]


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "success": True,
                "message": "Drug and contract data updated successfully",
                # "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class FSSDrugUpdateNotesView(generics.UpdateAPIView):
    queryset = FSSDrug.objects.all()
    serializer_class = FSSDrugNotesSerializerNotes
    permission_classes = [IsAuthenticated]


    # def put(self, request, *args, **kwargs):
    #     return self.update_drug(request)

    def patch(self, request, *args, **kwargs):
        return self.update_drug(request)

    def update_drug(self, request):
        # Extract 'id' and 'notes' from the request data
        drug_id = request.data.get('id')
        notes = request.data.get('notes')

        # Validate the presence of 'id' and 'notes'
        if not drug_id or notes is None:
            return Response(
                {
                    "success": False,
                    "message": "Both 'id' and 'notes' must be provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch the drug record by 'id'
            drug = FSSDrug.objects.get(id=drug_id)
            # Update the 'notes' field
            drug.notes = notes
            # Save the changes
            drug.save()

            # Serialize the updated drug
            serializer = self.get_serializer(drug)

            return Response(
                {
                    "success": True,
                    "message": "Drug data updated successfully",
                    # "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except FSSDrug.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Drug with the provided ID does not exist."
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Failed to update drug: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FOIADrugUpdateNotesView(generics.UpdateAPIView):
    queryset = FOIAUniqueNDCData.objects.all()
    serializer_class = FOIADrugNotesSerializerNotes
    permission_classes = [IsAuthenticated]


    # def put(self, request, *args, **kwargs):
    #     return self.update_drug(request)

    def patch(self, request, *args, **kwargs):
        return self.update_drug(request)

    def update_drug(self, request):
        # Extract 'id' and 'notes' from the request data
        drug_id = request.data.get('id')
        notes = request.data.get('notes')

        # Validate the presence of 'id' and 'notes'
        if not drug_id or notes is None:
            return Response(
                {
                    "success": False,
                    "message": "Both 'id' and 'notes' must be provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch the drug record by 'id'
            drug = FOIAUniqueNDCData.objects.get(id=drug_id)
            # Update the 'notes' field
            drug.notes = notes
            # Save the changes
            drug.save()

            # Serialize the updated drug
            serializer = self.get_serializer(drug)

            return Response(
                {
                    "success": True,
                    "message": "Drug data updated successfully",
                    # "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except FSSDrug.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Drug with the provided ID does not exist."
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Failed to update drug: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class FSSVendorUpdateNotesView(generics.UpdateAPIView):
    queryset = FSSVendor.objects.all()
    serializer_class = FSSVendorNotesSerializerNotes
    permission_classes = [IsAuthenticated]


    # def put(self, request, *args, **kwargs):
    #     return self.update_drug(request)

    def patch(self, request, *args, **kwargs):
        return self.update_drug(request)

    def update_drug(self, request):
        # Extract 'id' and 'notes' from the request data
        vendor_id = request.data.get('id')
        notes = request.data.get('notes')

        # Validate the presence of 'id' and 'notes'
        if not vendor_id or notes is None:
            return Response(
                {
                    "success": False,
                    "message": "Both 'id' and 'notes' must be provided."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Fetch the drug record by 'id'
            drug = FSSVendor.objects.get(id=vendor_id)
            # Update the 'notes' field
            drug.notes = notes
            # Save the changes
            drug.save()

            # Serialize the updated drug
            serializer = self.get_serializer(drug)

            return Response(
                {
                    "success": True,
                    "message": "Vendor data updated successfully",
                    # "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except FSSDrug.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Drug with the provided ID does not exist."
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"Failed to update drug: {str(e)}"
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
class ManufacturerUpdateView(generics.GenericAPIView):
    serializer_class = ManufacturerUpdateSerializer
    permission_classes = [IsAuthenticated]


    def put(self, request, *args, **kwargs):
        return self.update_manufacturers(request)


    def update_manufacturers(self, request):
        data = request.data
        drug_id = data.get('id')

        if not drug_id:
            return Response(
                {"success": False, "message": "'id' must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        manufactured_by_name = data.get('manufactured_by')
        manufactured_for_name = data.get('manufactured_for')
        manufacture_address = data.get('manufactured_address')  # New field for manufacture address

        try:
            drug = FSSDrug.objects.get(id=drug_id)

            if manufactured_by_name is not None:
                manufactured_by, created = Manufacturer.objects.get_or_create(name=manufactured_by_name)
                drug.manufactured_by = manufactured_by

            if manufactured_for_name is not None:
                manufactured_for, created = Manufacturer.objects.get_or_create(name=manufactured_for_name)
                drug.manufactured_for = manufactured_for

            if manufacture_address is not None:
                if drug.manufactured_by:
                    # Check if the address is different to avoid unnecessary save operations
                    if drug.manufactured_by.address != manufacture_address:
                        drug.manufactured_by.address = manufacture_address
                        drug.manufactured_by.save()
                else:
                    return Response(
                        {"success": False, "message": "Manufactured by must be set before updating the address."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            drug.save()

            return Response(
                {"success": True, "message": "Manufacturer information updated successfully"},
                status=status.HTTP_200_OK
            )
        except FSSDrug.DoesNotExist:
            return Response(
                {"success": False, "message": "Drug not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"success": False, "message": f"Failed to update drug: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FOIAMonthlyStatsFileUploadView(generics.GenericAPIView):
    serializer_class = FOIAMonthlyStatsFileUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, *args, **kwargs):
        serializer = FOIAMonthlyStatsFileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = request.FILES['file']

            # Read file content and pass to Celery task
            file_data = file.read()

            #Trigger Celery task to process CSV in the background
            #insert_foia_monthly_status_async_task.delay(file_data)
            
            insert_foia_monthly_status_task(file_data)

            return Response({
                "status": "success",
                "message": "File is being processed. The data will be inserted soon."
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)