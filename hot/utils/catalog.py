""" service document retrieval and extraction """

import json
import requests

from token import get_auth_document


def get_service_document(auth_doc, service_name):

    for service in auth_doc['access']['serviceCatalog']:
        if service['name'] == service_name:
            return service
    else:
        return None


def get_default_region(auth_doc):

    default_region = auth_doc['access']['user'].get('RAX-AUTH:defaultRegion')

    if default_region:
        return default_region
    else:
        return None


def get_service_endpoint(region, service_name, endpoint, username,
                         password=None, api_key=None):

    auth_doc = get_auth_document(endpoint, username, password=password,
                                 api_key=api_key)

    service = get_service_document(auth_doc, service_name)

    if not region:
        region = get_default_region(auth_doc)

    if service:
        for endpoint in service.get('endpoints', []):
            if endpoint.get('region', '').lower() == region.lower():
                return endpoint.get('publicURL', None)
    else:
        return None
