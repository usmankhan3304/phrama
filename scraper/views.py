# views.py
from .fetch_data.scraper import PharmaScraper
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import *
from rest_framework import viewsets
from .models import *
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from scraper.fetch_data.insert_foia_drug_data_from_file import FetchFoiaFile
from scraper.fetch_data.insert_dod_data import InsertDODDrugData
from django.utils import timezone
from .task import *
import logging

logger = logging.getLogger('scraping')

class VendorViewSet(viewsets.ModelViewSet):
    queryset = FSSVendor.objects.all()
    serializer_class = VendorSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = FSSContract.objects.all()
    serializer_class = ContractSerializer


class DrugViewSet(viewsets.ModelViewSet):
    queryset = FSSDrug.objects.all()
    serializer_class = DrugSerializer


class PricingViewSet(viewsets.ModelViewSet):
    queryset = FSSPricing.objects.all()
    serializer_class = PricingSerializer


class PotentialLeadViewSet(viewsets.ModelViewSet):
    queryset = PotentialLead.objects.all()
    serializer_class = PotentialLeadSerializer


# pharma_scraper/views.py
class PharmaScraperView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            
            #locally
            #run_pharma_scraper()
            
            #Production
            run_pharma_scraper_async.delay()  
            return Response(
                {"success": True, "message": "Scraper execution started. Please check the status later."},
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class InsertScrapedDataView(APIView):
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        #locally
        #insert_scraped_data()

        #Production
        insert_scraped_data_async.delay()
        return Response(
            {"success": True, "message": "Inserting scraped data started..."},
            status=status.HTTP_202_ACCEPTED,
        )


class InsertFOIADataView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        #locally
        #foia_data_insert = FetchFoiaFile() 
        #foia_data_insert.run()
        
        #Production
        insert_foia_drug_data_async.delay()
        return Response(
            {"success": True, "message": "Inserting FOIA data started..."},
            status=status.HTTP_202_ACCEPTED,
        )


class InsertDODDrugDataView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        #locally
        # dod_drug_data = InsertDODDrugData() 
        # dod_drug_data.insert_dod_data()

        
        #Production
        insert_dod_drug_data_async.delay()
        return Response(
            {"success": True, "message": "Inserting DOD data started..."},
            status=status.HTTP_202_ACCEPTED,
        )


# class StopScrapingView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def post(self, request, *args, **kwargs):
#         # Retrieve the latest scraping task status from the database
#         latest_scraping_task = ScrapingStatus.objects.filter(status='running').order_by('-start_time').first()

#         if latest_scraping_task:
#             # Stop the task using its task ID
#             message = stop_task(latest_scraping_task.task_id)
#             latest_scraping_task.status = 'stopped'
#             latest_scraping_task.end_time = timezone.now()
#             latest_scraping_task.save()
#             logger.info(f"Stopping the latest scraping task: {latest_scraping_task.task_id}")
#             return Response(
#                 {"success": True, "message": message},
#                 status=status.HTTP_202_ACCEPTED
#             )
#         else:
#             message = "The latest scraping task has already stopped or no task found."
#             logger.info(message)
#             return Response(
#                 {"success": False, "message": message},
#                 status=status.HTTP_200_OK
#             )
            

class StopScrapingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Retrieve all running scraping tasks from the database
        running_scraping_tasks = ScrapingStatus.objects.filter(status='running').order_by('-start_time')

        if running_scraping_tasks.exists():
            stopped_tasks = []

            # Stop all running tasks using their task IDs
            for task in running_scraping_tasks:
                # Stop the task by revoking it via its task ID
                message = stop_task(task.task_id)  # Assuming stop_task is a wrapper around Celery's revoke
                task.status = 'stopped'
                task.end_time = timezone.now()
                task.save()
                logger.info(f"Stopping the scraping task: {task.task_id}")
                stopped_tasks.append(task.task_id)

            return Response(
                {"success": True, "message": f"Stopped tasks: {stopped_tasks}"},
                status=status.HTTP_202_ACCEPTED
            )
        else:
            message = "No running tasks found."
            logger.info(message)
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_200_OK
            )




