##import libraries needed for functions to run

import random
import math
import urllib
import urllib.parse
from hashlib import sha1
import hmac
import requests
import datetime
import base64
import json
import time

##create the 'ayx_auth' function that generates the signed url for our requests

def ayx_auth(apikey,apisecret,url,method):

    ##generate and concatenate the required oauth parameters

    oauth_nonce = str(random.randint(0,51543575)+654987)

    oauth_timestamp = str(int(time.time()))

    values = str('oauth_consumer_key='+apikey+'&'+'oauth_nonce='+oauth_nonce+'&'+'oauth_signature_method=HMAC-SHA1'+'&'+'oauth_timestamp='+oauth_timestamp+'&'+'oauth_version=1.0')

    ##percent encode the value string and the url

    percent_values = urllib.parse.quote(values, safe='')

    percent_url = urllib.parse.quote(url, safe='')

    ##create signature_base_string and encode as bytes

    Signature_Base_String = method+'&'+percent_url+'&'+percent_values

    ##encode the signature and secret as bytes

    raw =  bytes(Signature_Base_String, 'utf-8')

    key = bytes(apisecret+'&','utf-8')

    ##apply hmac-sha1 encryption to generate oauth signature

    hashed = hmac.new(key, raw, sha1)

    raw = base64.urlsafe_b64encode(hashed.digest())
    oauth_signature = raw.decode()

    oauth_signature = oauth_signature.replace('-','+')
    oauth_signature = oauth_signature.replace('_', '/')

    oauth_signature = urllib.parse.quote(oauth_signature, safe='')

    oauth_signature = 'oauth_signature='+oauth_signature

    ##generate our signed url and pass this out of function

    url = url+'?'+values+'&'+oauth_signature

    return url

##create a function that allows you to execute a workflow/application on the Alteryx Gallery, ayx_auth function created above is used in here

def execute_workflow(apikey,apisecret,baseurl,workflowid,payload):

    ##create the url required as per this call, this includes the workflow id passed by the user

    url = baseurl+'api/v1/workflows/'+workflowid+'/jobs/'
    method = 'POST'

    ##use the ayx_auth function created above to create a signed url

    url = ayx_auth(apikey,apisecret,url,method)

    ##make the initial api call to trigger the job to run

    headers = {'Content-type': 'application/json'}

    apicall = requests.post(url,data=payload,headers=headers)

    ##only proceed if the respose from the api was 200 (i.e. things are fine!)

    if apicall.status_code == 200:

        ##retrieve the jobid from the response

        jsonresponse = apicall.json()

        jobid = jsonresponse['id']

        ##create the url required to check the status of the generated job

        url = baseurl+'api/v1/jobs/'+jobid+'/'
        method = 'GET'

        ##use the ayx_auth function created above to create a signed url

        signedurl = ayx_auth(apikey,apisecret,url,method)

        ##make the request to fetch the job status

        apicall = requests.get(signedurl)
        apiresponse = apicall.json()

        ##build in a loop to keep fetching the job status until it is set to complete

        while apiresponse['status'] != 'Completed':

            ##hold the call for 5 seconds so that we aren't constantly querying

            time.sleep(5)

            ##use the ayx_auth function created above to create a signed url

            signedurl = ayx_auth(apikey,apisecret,url,method)

            ##make the request to fetch the job status

            apicall = requests.get(signedurl)

            ##check if the status code is 200 if not break the loop

            if apicall.status_code != 200:
                break
            apiresponse = apicall.json()

            ##once the call has returned the status 'completed' go and fetch the full apiresponse

        else:

            ##use the ayx_auth function created above to create a signed url

            signedurl = ayx_auth(apikey,apisecret,url,method)

            ##make the request to fetch the job status

            apicall = requests.get(signedurl)
            apiresponse = apicall.json()
            return apiresponse
    else:

        apiresponse = apicall.json()

        return apiresponse
