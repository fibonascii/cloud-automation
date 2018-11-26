from botocore.vendored import requests
import os


def get_access_token():
    """ Get client API Service Authorization token and store into sessionAttributes"""
    access_token_request_data = {
        "clientId": os.environ['CLIENT_SERVICE_ID'],
        "clientSecret": os.environ['CLIENT_SERVICE_SECRET']
    }
    access_token_url = '{}/api/v1/auth/token'.format(os.environ['CLIENT_SERVICE_URL'])
    access_token_headers = {'content-type': 'application/json'}

    get_token = requests.post(access_token_url, json=access_token_request_data, headers=access_token_headers,
                              verify=False)

    if get_token.ok:
        access_token_response = get_token.json()
        return access_token_response['data']['accessToken']
    # else:
    #    handle_session_end_request()


def make_loyalty_get_request(loyalty_rest_endpoint, client_service_token):
    
    request_headers = {'content-type': 'application/json',
                       'authorization': 'bearer {}'.format(client_service_token)
                       }

    endpoint = loyalty_rest_endpoint
    response = requests.get(url=endpoint, headers=request_headers, verify=False)

    print(response.json())
    if response.ok:
        json_response = response.json()
        return json_response['data']
    # else:
    #    handle_session_end_request()


def make_loyalty_post_request(loyalty_rest_endpoint, client_service_token):
    request_headers = {'content-type': 'application/json',
                       'authorization': 'bearer {}'.format(client_service_token)
                       }

    endpoint = loyalty_rest_endpoint
    response = requests.post(url=endpoint, headers=request_headers, verify=False, data="")

    print(response.json())
    if response.ok:
        json_response = response.json()
        return json_response['data']
    # else:
    #    handle_session_end_request()
    



