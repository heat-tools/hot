
import os
import keystoneclient.v2_0.client as ksclient


class OSAuth(object):

    def __init__(self):
        self.creds = self.get_keystone_creds()
        self.keystone_client = ksclient.Client(**self.creds)

    def get_keystone_creds(self):
        creds = {}
        if os.environ.get('OS_AUTH_TOKEN'):
            creds['auth_url'] = os.environ['OS_AUTH_URL']
            creds['token'] = os.environ['OS_AUTH_TOKEN']
        else:
            creds['username'] = os.environ['OS_USERNAME']
            creds['password'] = os.environ['OS_PASSWORD']
            creds['auth_url'] = os.environ['OS_AUTH_URL']
            creds['tenant_id'] = os.environ['OS_TENANT_ID']
            creds['region_name'] = os.environ.get('OS_REGION_NAME')
            if creds.get('region_name'):
                creds['region_name'] = creds['region_name'].upper()
        return creds

    def get_token(self):
        return self.keystone_client.auth_token

    def get_heat_url(self):
        if os.environ.get('HEAT_URL'):
            return os.environ.get('HEAT_URL')
        else:
            heat_url = self.keystone_client.service_catalog.url_for(
                service_type='orchestration',
                endpoint_type='publicURL')
            return heat_url
