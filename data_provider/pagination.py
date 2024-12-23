# pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsPagination(PageNumberPagination):
    page_size = 100  # Define how many items per page
    page_size_query_param = 'page_size'  # Allow client to override the page size with a query parameter
    max_page_size = 1000  # Maximum limit of the page size

    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'message': 'Data retrieved successfully',
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

class DashboardResultsPagination(PageNumberPagination):
    page_size = 100  # Define how many items per page
    page_size_query_param = 'page_size'  # Allow client to override the page size with a query parameter
    max_page_size = 1000  # Maximum limit of the page size

    def get_paginated_response(self, data, percentage=None):
        return Response( {
            'success': True,
            'message': 'Data retrieved successfully',
            'count': self.page.paginator.count,
            'percentage': percentage,  # Include the percentage in the response
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

