from collections import defaultdict
import json
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from data_provider.pagination import StandardResultsPagination
from django.apps import apps
from django.db.models import ForeignKey, ManyToOneRel, ManyToManyRel, OneToOneRel
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from .task import populate_consolidated_table
from .models import *
import openpyxl
from django.http import HttpResponse
from rest_framework.decorators import action

from scraper.models import (
    FSSDrug,
    FOIAUniqueNDCData,
    FOIADrugsData,
    FOIAStationData,
    DODDrugData,
    PotentialLead,
    AccessDrugShortageData,
    AsphDrugShortageData,
    FSSContract,
    FSSVendor,
    Manufacturer,
    FSSPricing,
)

from .serializers import *
from django.db.models import Subquery, OuterRef, Q

class AdvancedSearchView(APIView):
    pagination_class = StandardResultsPagination
    permission_classes = [IsAuthenticated]

    # Define the source-to-model mapping
    SOURCE_MODEL_MAP = {
        "FSS": [
            ("scraper", "FSSVendor"),
            ("scraper", "FSSContract"),
            ("scraper", "Manufacturer"),
            ("scraper", "FSSDrug"),
            ("scraper", "FSSPricing"),
        ],
        "FOIA": [
            ("scraper", "FOIAUniqueNDCData"),
            ("scraper", "FOIADrugsData"),
            ("scraper", "FOIAStationData"),
            ("scraper", "Manufacturer"),
        ],
        "DOD": [("scraper", "DODDrugData")],
        "Potential Lead": [("scraper", "PotentialLead")],
        "Access Drug Shortage": [("scraper", "AccessDrugShortageData")],
        "Asph Drug Shortage": [("scraper", "AsphDrugShortageData")],
    }

    # Define available query types
    QUERY_LOOKUP_MAP = {
        "Contains": "icontains",
        "Greater Than": "gt",
        "Less Than": "lt",
        "Equal": "exact",
        "Less Than Equal To": "lte",
        "Not Equal To": "ne",  # Will handle this separately as Django doesn't have a direct lookup for "not equal"
        "Greater Than Equal To": "gte",
    }

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "source",
                openapi.IN_QUERY,
                description="The data source to search (e.g., FSSDrug, FOIA, DOD, etc.).",
                type=openapi.TYPE_STRING,
                enum=[
                    "FSS",
                    "FOIA",
                    "DOD",
                    "Potentia lLead",
                    "Access Drug Shortage",
                    "Asph Drug Shortage",
                ],
                required=True,
            ),
            openapi.Parameter(
                "column",
                openapi.IN_QUERY,
                description="The column to filter by.",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "query",
                openapi.IN_QUERY,
                description="The type of query to perform.",
                type=openapi.TYPE_STRING,
                enum=list(
                    QUERY_LOOKUP_MAP.keys()
                ),  # Define the choices for this parameter
                required=True,
            ),
            openapi.Parameter(
                "value",
                openapi.IN_QUERY,
                description="The value to match against the selected column.",
                type=openapi.TYPE_STRING,
                required=True,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        source = request.query_params.get("source")
        column = request.query_params.get("column")
        match_query = request.query_params.get("query")
        value = request.query_params.get("value")

        # Validate the source
        if source not in self.SOURCE_MODEL_MAP:
            return Response(
                {
                    "success": False,
                    "message": "Invalid source provided.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Identify the model and column
        model_class, filter_key = None, None
        for app_label, model_name in self.SOURCE_MODEL_MAP[source]:
            model_class = apps.get_model(app_label=app_label, model_name=model_name)

            # If the column is in the model or related fields
            if hasattr(model_class, column):
                filter_key = column
                break
            else:
                # Check if it's a ForeignKey field and if the related model has the column
                for field in model_class._meta.fields:
                    if field.is_relation and hasattr(field.related_model, column):
                        filter_key = f"{field.name}__{column}"
                        model_class = field.related_model
                        break

        if not filter_key:
            return Response(
                {
                    "success": False,
                    "message": f"Column '{column}' not found in the source '{source}'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Translate the dropdown option to Django query lookup
        lookup_type = self.QUERY_LOOKUP_MAP.get(match_query)
        if not lookup_type:
            return Response(
                {
                    "success": False,
                    "message": "Invalid query type provided.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build the query
        query_filter = {}
        if lookup_type == "ne":
            query = ~Q(**{f"{filter_key}__exact": value})
        else:
            query_filter[f"{filter_key}__{lookup_type}"] = value

        # Execute the query with pagination
        try:
            results = model_class.objects.filter(**query_filter)
            paginator = self.pagination_class()
            paginated_results = paginator.paginate_queryset(results, request)
            serializer_class = self.get_serializer_class(model_class)
            serializer = serializer_class(paginated_results, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred while processing the request: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_serializer_class(self, model_class):
        # Logic to dynamically get the serializer class based on the model
        model_name = model_class.__name__
        serializer_name = f"{model_name}Serializer"
        try:
            return globals()[serializer_name]
        except KeyError:
            raise ValueError(f"Serializer for model {model_name} not found.")


class GetColumnsView(APIView):
    permission_classes = [IsAuthenticated]

    # Define the source-to-model mapping
    SOURCE_MODEL_MAP = {
        "FSS": [
            ("scraper", "FSSVendor"),
            ("scraper", "FSSContract"),
            ("scraper", "Manufacturer"),
            ("scraper", "FSSDrug"),
            ("scraper", "FSSPricing"),
        ],
        "FOIA": [
            ("scraper", "FOIAUniqueNDCData"),
            ("scraper", "FOIADrugsData"),
            ("scraper", "FOIAStationData"),
            ("scraper", "Manufacturer"),
        ],
        "DOD": [("scraper", "DODDrugData")],
        "Potential Lead": [("scraper", "PotentialLead")],
        "Access Drug Shortage": [("scraper", "AccessDrugShortageData")],
        "Asph Drug Shortage": [("scraper", "AsphDrugShortageData")],
    }

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "source",
                openapi.IN_QUERY,
                description="The data source to search (e.g., FSSDrug, FOIA, DOD, etc.).",
                type=openapi.TYPE_STRING,
                enum=[
                    "FSS",
                    "FOIA",
                    "DOD",
                    "Potential Lead",
                    "Access Drug Shortage",
                    "Asph Drug Shortage",
                ],
                required=True,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        source = request.query_params.get("source")

        try:
            # Get the list of model names associated with the source
            model_infos = self.SOURCE_MODEL_MAP.get(source)

            if not model_infos:
                return Response(
                    {
                        "success": False,
                        "message": "Invalid source provided.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Set to store unique columns
            columns_set = set()

            for model_info in model_infos:
                app_label, model_name = model_info

                # Get the model class from the app registry
                model = apps.get_model(app_label=app_label, model_name=model_name)

                # Retrieve all fields for the model, excluding 'id' fields, foreign keys, and reverse relations
                fields = [
                    field.name
                    for field in model._meta.get_fields()
                    if not isinstance(
                        field, (ForeignKey, ManyToOneRel, ManyToManyRel, OneToOneRel)
                    )
                    and field.name != "id"
                ]

                # Add the fields to the columns_set
                columns_set.update(fields)

            # Convert set to a sorted list to ensure consistent ordering
            columns_list = sorted(columns_set)

            return Response(
                {
                    "success": True,
                    "results": columns_list,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            # Handle unexpected errors
            return Response(
                {
                    "success": False,
                    "message": f"An error occurred while processing the request: {str(e)}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FSSDrugSearchAPIView(viewsets.ModelViewSet):
    serializer_class = FSSDrugSearchInputSerializer
    pagination_class = StandardResultsPagination 
    permission_classes = [IsAuthenticated]
    
    def apply_general_filters(self, filters, queryset):
        queries = Q()
        for filter_item in filters:
            frontend_field = filter_item['field']
            condition = filter_item['condition']
            value = filter_item['value']

            field = FIELD_LOOKUP.get(frontend_field)
            if not field:
                continue  
            
            lookup = CONDITION_LOOKUP.get(condition)
            if lookup:
                queries &= Q(**{f"{field}__{lookup}": value})

        return queryset.filter(queries)

    def apply_price_filters(self, filters, queryset):
        latest_pricing = FSSPricing.objects.filter(drug=OuterRef('pk')).order_by('-price_start_date')
        queryset = queryset.annotate(
            latest_price=Subquery(latest_pricing.values('price')[:1]),
            latest_price_type=Subquery(latest_pricing.values('price_type')[:1]),
            latest_price_start_date=Subquery(latest_pricing.values('price_start_date')[:1]),
            latest_price_stop_date=Subquery(latest_pricing.values('price_stop_date')[:1]),
            latest_non_taa_compliance=Subquery(latest_pricing.values('non_taa_compliance')[:1])
        )

        for filter_item in filters:
            frontend_field = filter_item['field']
            condition = filter_item['condition']
            value = filter_item['value']

            field_mapping = {
                "Price": "latest_price",
                "Price Type": "latest_price_type",
                "Price Start Date": "latest_price_start_date",
                "Price Stop Date": "latest_price_stop_date",
                "Non-TAA Compliance": "latest_non_taa_compliance",
            }
            field = field_mapping.get(frontend_field)
            if not field:
                continue

            if condition == "Equal":
                queryset = queryset.filter(**{f"{field}__exact": value})
            elif condition == "Not Equal To":
                queryset = queryset.exclude(**{f"{field}__exact": value})
            elif condition == "Greater Than":
                queryset = queryset.filter(**{f"{field}__gt": value})
            elif condition == "Less Than":
                queryset = queryset.filter(**{f"{field}__lt": value})

        return queryset
    
    def map_fields(self,fields):
        """ Maps frontend field names to database field names. """
        return [COLUMN_FIELD_MAPPING.get(field) for field in fields if COLUMN_FIELD_MAPPING.get(field)]


    def create_dynamic_serializer(self, fields):
        if not fields:  # If no fields are provided, include all fields by default
            fields = ['trade_name', 'package_description', 'latest_price', 'latest_price_type', 
                    'latest_price_start_date', 'latest_price_stop_date', 'latest_non_taa_compliance']
        
        # Map the requested columns to valid fields
        mapped_fields = self.map_fields(fields)
        
        # Ensure all requested fields are included
        if 'price_type' not in mapped_fields and 'Price Type' in fields:
            mapped_fields.append('price_type')

        return type('DynamicFSSDrugSerializer', (FSSDrugSerializer,), {
            'Meta': type('Meta', (object,), {
                'model': FSSDrug,
                'fields': mapped_fields
            })
        })

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filters = serializer.validated_data['filters']
        requested_columns = serializer.validated_data.get('columns', [])

        # Separate price-related filters from general filters
        price_filters = [f for f in filters if f['field'] in ['Price', 'Price Type', 'Price Start Date', 'Price Stop Date', 'Non-TAA Compliance']]
        general_filters = [f for f in filters if f not in price_filters]

        # Apply filters
        results = FSSDrug.objects.all()
        results = self.apply_general_filters(general_filters, results)

        if not results.exists():
            return Response({"success": True, "message": "No data found", "count": 0, "results": []}, status=status.HTTP_200_OK)

        results = self.apply_price_filters(price_filters, results)

        if not results.exists():
            return Response({"success": True, "message": "No data found", "count": 0, "results": []}, status=status.HTTP_200_OK)

        # Apply pagination
        # paginator = self.pagination_class()
        page = self.paginate_queryset(results)
        
        if page is not None:
            if requested_columns:
                dynamic_serializer_class = self.create_dynamic_serializer(requested_columns)
                context = {'request': request, 'requested_fields': requested_columns}
                output_serializer = dynamic_serializer_class(page, many=True, context=context)
                return self.get_paginated_response(output_serializer.data)
            else:
                output_serializer = FSSDrugSerializer(page, many=True)
                return self.get_paginated_response(output_serializer.data)
        
        # If no pagination is applied
        if requested_columns:
            dynamic_serializer_class = self.create_dynamic_serializer(requested_columns)
            output_serializer = dynamic_serializer_class(results, many=True)
        else:
            output_serializer = FSSDrugSerializer(results, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class ConsolidatedDrugSearchAPIView(viewsets.ModelViewSet):
    serializer_class = FSSDrugSearchInputSerializer  
    pagination_class = StandardResultsPagination 
    permission_classes = [IsAuthenticated]

    def apply_general_filters(self, filters, queryset):
        queries = Q()
        for filter_item in filters:
            frontend_field = filter_item['field']
            condition = filter_item['condition']
            value = filter_item['value']

            field = FIELD_LOOKUP.get(frontend_field)
            if not field:
                continue  

            lookup = CONDITION_LOOKUP.get(condition)
            if lookup:
                queries &= Q(**{f"{field}__{lookup}": value})

        return queryset.filter(queries)

    def apply_price_filters(self, filters, queryset):
        latest_pricing = ConsolidatedDrugPrice.objects.filter(drug=OuterRef('pk')).order_by('-price_start_date')
        queryset = queryset.annotate(
            latest_price=Subquery(latest_pricing.values('price')[:1]),
            latest_price_type=Subquery(latest_pricing.values('price_type')[:1]),
            latest_price_start_date=Subquery(latest_pricing.values('price_start_date')[:1]),
            latest_price_stop_date=Subquery(latest_pricing.values('price_stop_date')[:1]),
            latest_non_taa_compliance=Subquery(latest_pricing.values('non_taa_compliance')[:1])
        )

        for filter_item in filters:
            frontend_field = filter_item['field']
            condition = filter_item['condition']
            value = filter_item['value']

            field_mapping = {
                "Price": "latest_price",
                "Price Type": "latest_price_type",
                "Price Start Date": "latest_price_start_date",
                "Price Stop Date": "latest_price_stop_date",
                "Non-TAA Compliance": "latest_non_taa_compliance",
            }
            field = field_mapping.get(frontend_field)
            if not field:
                continue

            if condition == "Equal":
                queryset = queryset.filter(**{f"{field}__exact": value})
            elif condition == "Not Equal To":
                queryset = queryset.exclude(**{f"{field}__exact": value})
            elif condition == "Greater Than":
                # Exclude null values when applying 'Greater Than' filter
                queryset = queryset.exclude(**{f"{field}__isnull": True}).filter(**{f"{field}__gt": value})
            elif condition == "Less Than":
                # Exclude null values when applying 'Less Than' filter
                queryset = queryset.exclude(**{f"{field}__isnull": True}).filter(**{f"{field}__lt": value})
            elif condition == "Greater Than Equal To":
                # Exclude null values when applying 'Greater Than or Equal To' filter
                queryset = queryset.exclude(**{f"{field}__isnull": True}).filter(**{f"{field}__gte": value})
            elif condition == "Less Than Equal To":
                # Exclude null values when applying 'Less Than or Equal To' filter
                queryset = queryset.exclude(**{f"{field}__isnull": True}).filter(**{f"{field}__lte": value})

        return queryset

    def map_fields(self, fields):
        """ Maps frontend field names to database field names. """
        return [COLUMN_FIELD_MAPPING.get(field) for field in fields if COLUMN_FIELD_MAPPING.get(field)]

    def create_dynamic_serializer(self, fields):
        if not fields:  
            fields = ['trade_name', 'generic_name', 'package_description', 'price', 'price_type', 
                      'price_start_date', 'price_stop_date', 'non_taa_compliance', 'source']
        
        # Map the requested columns to valid fields
        mapped_fields = self.map_fields(fields)

        return type('DynamicConsolidatedDrugSerializer', (ConsolidatedDrugSerializer,), {
            'Meta': type('Meta', (object,), {
                'model': ConsolidatedDrugData,
                'fields': mapped_fields
            })
        })

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        filters = serializer.validated_data['filters']
        requested_columns = serializer.validated_data.get('columns', [])

        # Separate price-related filters from general filters
        price_filters = [f for f in filters if f['field'] in ['Price', 'Price Type', 'Price Start Date', 'Price Stop Date', 'Non-TAA Compliance']]
        general_filters = [f for f in filters if f not in price_filters]

        # Apply filters
        results = ConsolidatedDrugData.objects.all()
        results = self.apply_general_filters(general_filters, results)

        if not results.exists():
            return Response({"success": True, "message": "No data found", "count": 0, "results": []}, status=status.HTTP_200_OK)

        results = self.apply_price_filters(price_filters, results)

        if not results.exists():
            return Response({"success": True, "message": "No data found", "count": 0, "results": []}, status=status.HTTP_200_OK)

        # Apply pagination
        page = self.paginate_queryset(results)
        
        if page is not None:
            if requested_columns:
                dynamic_serializer_class = self.create_dynamic_serializer(requested_columns)
                context = {'request': request, 'requested_fields': requested_columns}
                output_serializer = dynamic_serializer_class(page, many=True, context=context)
                return self.get_paginated_response(output_serializer.data)
            else:
                output_serializer = ConsolidatedDrugSerializer(page, many=True)
                return self.get_paginated_response(output_serializer.data)
        
        # If no pagination is applied
        if requested_columns:
            dynamic_serializer_class = self.create_dynamic_serializer(requested_columns)
            output_serializer = dynamic_serializer_class(results, many=True)
        else:
            output_serializer = ConsolidatedDrugSerializer(results, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=["post"])
    def export_to_excel(self, request, *args, **kwargs):
        """
        Export the filtered Consolidated drug data to an Excel file using a POST request with filters in the request body.
        """
        try:
            # Retrieve filters from the POST request body
            filters = request.data.get('filters', [])
            
            # Separate price-related filters from general filters
            price_filters = [f for f in filters if f['field'] in ['Price', 'Price Type', 'Price Start Date', 'Price Stop Date', 'Non-TAA Compliance']]
            general_filters = [f for f in filters if f not in price_filters]

            # Apply filters to the queryset
            queryset = ConsolidatedDrugData.objects.all()
            queryset = self.apply_general_filters(general_filters, queryset)
            queryset = self.apply_price_filters(price_filters, queryset)

            if not queryset.exists():
                return Response(
                    {"success": False, "message": "No data found to export"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Create a workbook and a worksheet
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Consolidated Drugs Data"

            # Define headers
            headers = ["Trade Name", "Generic Name", "Package Description", "Price", "Price Type", "Price Start Date", "Price Stop Date", "Non-TAA Compliance", "Source"]
            sheet.append(headers)

            # Write data to the worksheet
            for data in queryset:
                sheet.append([
                    data.trade_name,
                    data.generic_name,
                    data.package_description,
                    data.latest_price,
                    data.latest_price_type,
                    data.latest_price_start_date,
                    data.latest_price_stop_date,
                    data.latest_non_taa_compliance,
                    data.source,
                ])

            # Set the file name
            file_name = f"consolidated_drugs_data_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # Create a HTTP response with an Excel content type
            response = HttpResponse(
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            response["Content-Disposition"] = f"attachment; filename={file_name}"

            # Save the workbook to the response
            workbook.save(response)

            return response

        except Exception as e:
            return Response(
                {"success": False, "message": f"Error exporting data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




class PopulateConsolidatedTableView(APIView):
    def post(self, request, *args, **kwargs):
        
        # Trigger the background task
        populate_consolidated_table.delay()
        
        #For local
        #populate_consolidated_table()
        return Response({"message": "Population started successfully."}, status=status.HTTP_202_ACCEPTED)
