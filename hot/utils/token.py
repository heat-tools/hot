"""Functions for getting Auth Tokens from Racker Auth"""

import json
import requests


def get_token(endpoint, username, password=None, api_key=None):
    if "/v2.0" not in endpoint:
        endpoint = endpoint + "/v2.0"
    if "/tokens" not in endpoint:
        endpoint = endpoint + "/tokens"
    headers = {'Content-Type': 'application/json'}

    auth = {'username': username}
    if api_key is not None:
        prefix = 'RAX-KSKEY:apiKeyCredentials'
        auth['apiKey'] = api_key
        payload = {'auth': {prefix: auth}}
    elif password is not None:
        prefix = 'passwordCredentials'
        auth['password'] = password
        payload = {'auth': {prefix: auth}}
    else:
        raise AttributeError('No Password or APIKey Specified')

    response = requests.post(endpoint, data=json.dumps(payload),
                             headers=headers)

    response.raise_for_status()
    results = response.json()
    return results['access']['token']['id']
