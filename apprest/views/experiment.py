import logging

from django.core import serializers
from django.http import HttpResponse
from rest_framework import pagination, filters, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied

from rest_framework.generics import ListAPIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apprest.serializers.experiment import CalipsoExperimentSerializer
from apprest.services.experiment import CalipsoExperimentsServices
from apprest.utils.request import JSONResponse

from calipsoplus.settings_calipso import PAGE_SIZE_EXPERIMENTS, DYNAMIC_EXPERIMENTS_DATA_RETRIEVAL

import pdb

from django_filters.rest_framework import DjangoFilterBackend

service = CalipsoExperimentsServices()

logger = logging.getLogger(__name__)


class ExperimentsPagination(pagination.PageNumberPagination):
    page_size = PAGE_SIZE_EXPERIMENTS
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data,
            'page_size': self.page_size,
        })


class GetExperimentsByUserName(ListAPIView):
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = CalipsoExperimentSerializer
    pagination_class = ExperimentsPagination
    filter_backends = (filters.OrderingFilter, filters.SearchFilter, DjangoFilterBackend,)
    ordering_fields = ('subject', 'body', 'serial_number', 'beam_line', 'calipsouserexperiment__favorite',)
    ordering = ('serial_number',)
    search_fields = ('subject', 'body', 'serial_number', 'beam_line', 'calipsouserexperiment__favorite',)
    filter_fields = ('calipsouserexperiment__favorite',)

    def get_queryset(self):
        username = self.kwargs.get('username')
        if username == self.request.user.username:
            logger.debug('experiments get from db')
            experiments_list = service.get_user_experiments(username)
            return experiments_list
        else:
            raise PermissionDenied

    def get(self, request, *args, **kwargs):
        if DYNAMIC_EXPERIMENTS_DATA_RETRIEVAL == 0:
            return super(GetExperimentsByUserName, self).get(self, request, *args, **kwargs)
        else:
            username = self.kwargs.get('username')
            if username == self.request.user.username:

                query = {"page": request.GET.get('page'),
                         "ordering": request.GET.get('ordering'),
                         "search": request.GET.get('search'),
                         "calipsouserexperiment__favorite": request.GET.get('calipsouserexperiment__favorite')}

                experiments_list = service.get_external_user_experiments(username, query)

                return JSONResponse(experiments_list, status=status.HTTP_200_OK)
            else:
                raise PermissionDenied