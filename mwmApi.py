# Import requests for making API requests
import requests
import urllib3
urllib3.disable_warnings()
# Import for building urls
#import urllib.parse as urlparse
import urlparse
# Import for loading json into python dictionary
import json
import time

REQUEST_TIMEOUT = 300  # 5 minutes

HTTPS = "https"
PATH_BASE = "{hostname}/new/"
PATH_API_WEBSERVICE = "webservice/v4"
PATH_LOGIN = "/login/key/{client_identifier}/{session_timeout}"
PATH_LOGOUT = "/logout"
PATH_LOCATION_TREE = "locations/tree"
PATH_MANAGED_DEVICES = "devices/manageddevices"
PATH_OBSERVING_MANAGED_DEVICES = "devices/manageddevices/{boxId}/observingmanageddevices"
PATH_CLIENTS = "devices/clients"
PATH_CLIENT_CONN_STATS = "devices/clients/connectivitystats"
PATH_VIRTUAL_ACCESS_POINTS = "devices/aps"
PATH_ASSOCIATION_ANALYTICS = "analytics/associationdata/{start_time}/{end_time}"    # Path parameters
PATH_SSID_PROFILES = "templates/SSID_PROFILE"
PATH_CLIENT_CONN_TEST = "troubleshoot/clientconnectivity/sessions"
QUERY_FILTER = "filter=%s"
QUERY_LOCATION_ID = "locationid=%s"
QUERY_NODE_ID = "nodeid=%s"
QUERY_FILE_FORMAT = 'format="%s"'
QUERY_MAC_OBFUSCATE = 'tohashmac="%s"'

HEADER_JSON_CONTENT = {"Content-Type": "application/json"}


class MwmApi:

    def __init__(self, hostname, cookie_jar):
        """
        :param hostname: server hostname (Example: "training.mojonetworks.com")
        :return:
        """
        self.hostname = hostname
        self.cookie_jar = cookie_jar

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()
        self.hostname = None
        self.cookie_jar = None

    def request(self, relative_path='', query_parameters='', method="GET", body=None, url=None,
                headers=HEADER_JSON_CONTENT):
        """ Common function for making API calls and returning content

        :param relative_path: resource path to be queried ("devices/clients")
        :param query_parameters: ampersand(&) separated query parameters ("locationid=1&nodeid=1")
        :param method: request method ("GET", "PUT", "POST", "DELETE")
        :param body: request body as string (used for methods like POST, PUT)
        :param url: used to specify custom url (https://www.mojo.com/new/webservice/V4/devices/clients?locationid=1")
        :param headers: request headers
        :return: response object
        """
        if url is None:
            url = urlparse.urlunparse((
                HTTPS,                                                                  # "https"
                PATH_BASE.format(hostname=self.hostname) + PATH_API_WEBSERVICE,         # "training.mojonetworks.com/new/webservice/V4"
                relative_path,                                                          # "devices/clients"
                '',
                query_parameters,                                                       # "locationid=1&nodeid=1"
                ''
            ))
        print(self.cookie_jar)
        print(url)
        # Makes the request
        response = requests.request(
            method,                             # request method ("GET", "PUT", "POST", "DELETE")
            url,                                # constructed url
            timeout=REQUEST_TIMEOUT,            # timeout for request
            cookies=self.cookie_jar,            # session cookies to be passed after login
            data=body,                          # request body
            headers=headers,                    # headers to use ({"Content-Type": "application/json"})
            verify=False
        )
        #print(response)

        try:
            # raise exception for error HTTP status (4xx, 5xx)
            response.raise_for_status()
            return response

        except Exception as e:
            # Handle for error HTTP codes
            print("\nException: \n........................\n")
            print(e)
            return response

            #response_dict = response.json()
            #print("HTTP Error " + str(response_dict["status"]))
            #for error in response_dict["errors"]:
             #   print(error["errorCode"] + " => " + error["message"])
             #   print("DEBUG: " + error["moreInfo"])
        

    def login(self, client_identifier, session_timeout, kvs_service_data):
        """ Login to service

        :param client_identifier: string to identify caller
        :param session_timeout: session timeout in seconds
        :param kvs_service_data: kvs credentials (cname, keyId, keyValue)
        :return:
        """

        # POST request body
        auth_data = {
            "type": "apikeycredentials",
            "keyId": kvs_service_data["keyId"],
            "keyValue": kvs_service_data["keyValue"]
            #"exposedCustomerId": kvs_service_data["cname"]
        }
        print("Calling login...")
        response = self.request(
            PATH_LOGIN.format(client_identifier=client_identifier, session_timeout=session_timeout),
            method="POST",
            body=json.dumps(auth_data)
        )
        #print("Response: " + response)
        if response.status_code == requests.codes.ok:
            #print(response.cookies)
            self.cookie_jar = response.cookies
            return response.json()
        else:
            print("Unrecognised status for login" + str(response.status_code))
            raise
    
    def get_cookiejar_dict(self):
            return requests.utils.dict_from_cookiejar(self.cookie_jar)

    def set_cookiejar_from_dict(self, cookiejar_dict):
        self.cookie_jar = requests.utils.cookiejar_from_dict(cookiejar_dict);

    def logout(self):
        """ Logout from service """

        response = self.request(
            PATH_LOGOUT,
            method="POST"
        )

        if response.status_code == requests.codes.ok:
            return
        else:
            print("Unrecognised status for logout" + str(response.status_code))
            raise

    def get_ssid_profiles(self):
        """
        Fetch all SSID profiles
        
        """
        response = self.request(PATH_SSID_PROFILES)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for location tree fetch" + response.status_code)
		
    def get_location_tree(self):
        """ Fetch location tree

        :return: response object
        """
        response = self.request(PATH_LOCATION_TREE)
        
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for location tree fetch" + response.status_code)

    def get_managed_ap_devices(self, locid, active_devices_only = False):
        """ Fetch managed device with specified filter

        :return: response object
        """
        query = "nodeid=0&locationid="+str(locid)
        ap_mode_filter_value = {
            "property": "devicemode",
            "value": ["AP", "AP_SENSOR_COMBO"],
            "operator": "="
        }
        query = query + "&" + QUERY_FILTER % json.dumps(ap_mode_filter_value)
        if active_devices_only == True:
            active_filter_value = {
                    "property": "active",
                    "value": [True],
                    "operator": "="
            }
            query = query + "&" + QUERY_FILTER % json.dumps(active_filter_value)
        #print(query)

        response = self.request(PATH_MANAGED_DEVICES, query)
        print(response)
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for managed device fetch" + str(response.status_code))


    def get_clients(self, locid):
        """ Fetch managed device with specified filter

        :return: response object
        """

        filter_value = {
                    "property": "locationid",
                    "value": [locid],
                    "operator": "="
                }
        query = QUERY_FILTER % json.dumps(filter_value)

        response = self.request(PATH_CLIENTS, query)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for managed device fetch" + response.status_code)


    def get_virtual_aps(self):
        """ Fetch Virtual APs with specified filter

        :return: response object
        """

        # Virtual AP with (boxid = 1) OR (group = AUTHORIZED)
        filter_value = {
            "value": [
                {
                    "property": "boxid",
                    "value": [1],
                    "operator": "="
                },
                {
                    "property": "group",
                    "value": ['AUTHORIZED'],
                    "operator": "="
                }
            ],
            "operator": "OR"
        }
        query = QUERY_FILTER % json.dumps(filter_value)

        response = self.request(PATH_VIRTUAL_ACCESS_POINTS, query)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for virtual AP fetch" + response.status_code)

    def get_observing_managed_devices(self, boxid):
        print("Searching observing devices for boxid: " + str(boxid))
        query="isthirdradiosupported=true"
        response = self.request(PATH_OBSERVING_MANAGED_DEVICES.format(boxId=boxid), query)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for managed device fetch" + response.status_code)
        
    def start_client_conn_test(self, locid, target_boxid, client_boxid, test_profile_id):
        start_params = {
            'testProfileId': test_profile_id,
            'targetApBoxId': target_boxid,
            'targetClientBoxId': client_boxid
        }
        print(start_params)
        response = self.request(
            PATH_CLIENT_CONN_TEST,
            method="POST",
            query_parameters = "locationid="+str(locid),
            body=json.dumps(start_params)
        )
        print(response)
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status " + str(response.status_code))

        return None

    def get_client_conn_test_status(self, locid, session_id):
        query = "sessionid="+str(session_id)
        response = self.request(PATH_CLIENT_CONN_TEST, query)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for client conn test status" + str(response.status_code))

    def get_client_conn_test_result(self, session_id):
        path = PATH_CLIENT_CONN_TEST + "/"+str(session_id)+"?locationid=0"
        response = self.request(path)

        if response.status_code != requests.codes.ok:
            print("Unrecognised status for client conn test result: " + str(response.status_code))
            return {'rv': 1, 'error_string' : "Error reading test result"}

        tresult = response.json()
        return tresult

    def get_best_client_device_for_conn_test(self, target_boxid):
        cldlist = self.get_observing_managed_devices(target_boxid)
        print(cldlist)
        if cldlist == None or len(cldlist) == 0:
            return None
        for cld in cldlist:
            print("\n\nCLD:")
            print(cld)
            if "C130" not in cld['name']:
                continue
            if cld['boxId'] != target_boxid:
                return cld
        return None

    def convert_conn_test_result_to_text(self, tresult):
        if tresult == None or not isinstance(tresult, dict) or 'attempts' not in tresult:
            return None
        if len(tresult['attempts']) == 0:
            return None
        sout = None
        for attempt in tresult['attempts']:
            print("Attempt ID: " + str(attempt['attemptId']))
            aresult = attempt['attemptResult']
            rv = self.convert_conn_test_attemp_result_to_text(aresult)
            if rv == None:
                continue
            if rv['rv'] == 0:
                return rv['sout']
            sout = rv['sout']
        if sout != None:
            return sout
        
        return "Unable to read result. Please try again"
            
    def convert_conn_test_attemp_result_to_text(self, attempt):
        sout = ""
        basic = attempt['basic']
        #Association
        if 'association' in basic and len(basic['association']) > 0 and 'assocRespRecv' in basic['association'][0]:
            if basic['association'][0]['assocRespRecv']['errorCode'] == None:
                sout = sout + "Association successful. "
            else:
                sout = sout + "Association attempt failed. Reason for failure: " + str(basic['association'][0]['assocRespRecv']['errorCode'])
        else:
            sout = sout + "Unable to read association result. Please try again"
            return {'rv': 1, 'sout': sout}
        #Authentication
        #DHCP
        if 'dhcp' in basic and len(basic['dhcp']) > 0:
            dhcp = basic['dhcp'][0]
        elif 'dhcp' in attempt and 'dhcp' in attempt['dhcp'] and len(attempt['dhcp']['dhcp']) > 0:
            dhcp = attempt['dhcp']['dhcp'][0]
        else:
            sout = "Unable to read dhcp result. Please try again"
            return {'rv': 1, 'sout': sout}

        if 'dhcpFailed' in dhcp:
            sout = sout + "Could not obtain IP address from DHCP. Test failed."
            return {'rv': 1, 'sout': sout}

        if 'dhcpIp' in dhcp and dhcp['dhcpIp']['errorCode'] == None:
            sout = sout + "DHCP successful. Obtained IP address " + dhcp['dhcpIp']['value']
            if 'dhcpDefMask' in dhcp and dhcp['dhcpDefMask']['errorCode'] == None:
                sout = sout + ", subnet mask " + dhcp['dhcpDefMask']['value']
            if 'dhcpDefGw' in dhcp and dhcp['dhcpDefGw']['errorCode'] == None:
                sout = sout + ", default gateway I P " + dhcp['dhcpDefGw']['value']
            if 'dhcpLatency' in dhcp and dhcp['dhcpLatency']['errorCode'] == None and dhcp['dhcpLatency']['value'] != None:
                sout = sout + ". D H C P latency is " + str(int(round(float(dhcp['dhcpLatency']['value'])))) + " milli-seconds."
        else:
            sout = sout + " Failure in obtaining DHCP IP address"
            return {'rv': 1, 'sout': sout}
        #Gateway
        if 'defGwLatency' in dhcp and dhcp['defGwLatency']['errorCode'] == None and dhcp['defGwLatency']['value'] != None:
            sout = sout + " Default Gateway is reachable. Latency to default gateway is " + str(int(round(float(dhcp['defGwLatency']['value'])))) + " milli-seconds. "
        else:
            sout = sout + " Default gateway is not reachable. Test failed at this point."
            return {'rv': 1, 'sout': sout}

        #DNS
        if 'dnsServerIp' in dhcp and dhcp['dnsServerIp']['errorCode'] == None:
            dnsip = dhcp['dnsServerIp']['value']
        else:
            sout = sout + " Error, could not obtain D N S server IP from D H C P. Test failed"
            return {'rv': 1, 'sout': sout}

        if 'dnsServerLatency' in dhcp and dhcp['dnsServerLatency']['errorCode'] == None and dhcp['dnsServerLatency']['value'] != None:
            sout = sout + " Latency to DNS server " + dnsip + " is " + str(int(round(float(dhcp['dnsServerLatency']['value'])))) + " milli-seconds. "
        else:
            sout = sout + " Error, unable to detect DNS latency."
            return {'rv': 1, 'sout': sout}
        
        #WAN Latency
        if 'wanHostname' in dhcp and dhcp['wanHostname']['errorCode'] == None:
            wanhost = dhcp['wanHostname']['value']
            if 'wanLatency' in dhcp and dhcp['wanLatency']['errorCode'] == None and dhcp['wanLatency']['value'] != None:
                sout = sout + " Latency to wan host " + wanhost + " is " + str(int(round(float(dhcp['wanLatency']['value'])))) + " milli-seconds. "
        else:
            sout = sout + " Error, unable to detect WAN latency."
            return {'rv': 1, 'sout': sout}
        #Ping
        ping = []
        if 'ping' in basic and len(basic['ping']) > 0:
            ping = basic['ping']
        elif 'ping' in attempt and 'ping' in attempt['ping'] and len(attempt['ping']['ping']) > 0:
            ping = attempt['ping']['ping']
        else:
            ping = []
        for pingtest in ping: 
            if 'pingServerIp' in pingtest and 'pingServerLatency' in pingtest and pingtest['pingServerLatency']['value'] != None:
                sout = sout + " Ping test to host " + pingtest['pingServerIp']['value'] + " is successful with a latency of " + str(int(round(float(pingtest['pingServerLatency']['value'])))) + " milli-seconds. "

        sout = sout + "End of test result."
        return {'rv': 0, 'sout': sout}

    def do_client_conn_test_at_loc(self, locid):
        #Get the list of managed AP devices that are active
        resp = self.get_managed_ap_devices(locid, True)
        if "managedDevices" not in resp:
            return {'rv':1, 'error_string': "Internal error"}
        #print(resp)
        mdlist = resp['managedDevices']
        #Iterate over the list and select the first device that 
        #has a neighboring 3-radio AP to act as a client
        test_devices_found = False
        for md in mdlist:
            print(md)
            if "C130" not in md['name']:
                continue
            target_boxid = md['boxId']
            cld = self.get_best_client_device_for_conn_test(target_boxid)
            if cld != None:
                client_boxid = cld['boxId']
                print("\nFound client device with boxid: " + str(client_boxid))
                test_devices_found = True
                break
        if test_devices_found == False:
            return {'rv':1, 'error_string': "Suitable test devices not found at the location"}

        test_profile_id = 8
        tstatus = self.start_client_conn_test(locid, target_boxid, client_boxid, test_profile_id)
        if tstatus == None or 'sessionId' not in tstatus:
            return {'rv':1, 'error_string': "Unable to start connectivity test. Please try again"}
        session_id = tstatus['sessionId']
        wt = 0
        while wt < 120:
            print("Waiting for test result, polling after 10secs")
            time.sleep(5)
            wt += 10
            tstatus = self.get_client_conn_test_status(locid, session_id)
            print(tstatus)
            if tstatus == None or len(tstatus) == 0 or 'sessionStatus' not in tstatus[0]:
               return {'rv':1, 'error_string': "Unable to start connectivity test. Please try again"}
            if tstatus[0]['sessionStatus'] == "CL_CONNEC_COMPLETED":
                tresult = self.get_client_conn_test_result(session_id)
                print(tresult)
                result_text = self.convert_conn_test_result_to_text(tresult)
                if result_text != None:
                    return {'rv':0, 'result_text': result_text}

        return {'rv':1, 'error_string': "Timeout waiting for test result. Please try again"}


    def get_location_id_by_name(self, location):
        if location == None:
            return -2
        loctree = self.get_location_tree()
        loclist = loctree['locations']
        for loc in loclist:
            if location.lower() == loclist[loc]['name'].lower():
                return loclist[loc]['id']['id']

        return -2

    def get_device_count_at_location(self, locid):
        mdresp = self.get_managed_ap_devices(locid)
        active_devices = 0
        inactive_devices=0
        if mdresp != None and "managedDevices" in mdresp:
            mdlist = mdresp['managedDevices']
            for md in mdlist:
                if md['active'] == True:
                    active_devices = active_devices + 1
                else:
                    inactive_devices = inactive_devices + 1

        return {'active':active_devices, 'inactive':inactive_devices}

    def get_client_conn_stats_at_location(self, locid):
        time_secs = int(time.time()) - 300
        query = "locationid="+str(locid)+"&fromtime="+str(time_secs)+"&totime="+str(time_secs)

        response = self.request(PATH_CLIENT_CONN_STATS, query)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            print("Unrecognised status for managed device fetch" + response.status_code)

    def get_client_counts_at_loc(self, locid):
        cl_conn = self.get_client_conn_stats_at_location(locid)
        #print(cl_conn)
        cl_succ = 0
        cl_fail = 0
        if cl_conn != None:
            if 'successCount' in cl_conn:
                cl_succ = cl_conn['successCount']
            if 'failureCount' in cl_conn:
                cl_fail = cl_conn['failureCount']

        return {'successCount': cl_succ, 'failureCount': cl_fail}


if __name__ == '__main__':

    # MWM Server API instance
    #host = "alpha-mwm.mojonetworks.com"
    host = "mwm-at13004.mojonetworks.com"
    #host = "mwm-l3stagingblr.dt.airtightnw.com"
    mwm_api = MwmApi(host, None)

    # Login to MWM using KVS
    client = "api-client-alexa"
    login_timeout = "3000"
    #kvs_auth_data = {
    #    "keyId": "KEY-ATN19-10",
    #    "keyValue": "850151c6cc4860e593e75853abbec811",
    #    "cname": "ATN19",
    #}
    #Corp
    #kvs_auth_data = {
    #    "keyId": "KEY-ATN9-11",
    #    "keyValue": "0abc2f8664b141f80ebc406289579320",
    #    "cname": "ATN9"
    #}
    #Sinan Tunc API key
    kvs_auth_data = {
        "keyId": "KEY-ATN123464-312", # This key id is invalid. Replace this with your key-id
        "keyValue": "8790470ca82fa9112345eddee4473fa7", # This key is invalid - replace this with your key
    }
    print("Calling login...........")
    print(mwm_api.login(client, login_timeout, kvs_auth_data))
    print("After login........\n\n")
    #tresult = mwm_api.get_client_conn_test_result(64)
    #print(tresult)
    #result_text = mwm_api.convert_conn_test_result_to_text(tresult)
    #print(result_text)
    #exit()
    #cdict = mwm_api.get_cookiejar_dict()
    #print(cdict)
    #print("After cookie jar json ....\n\n")
    #Get clients
    print("Getting clients...........")
    print(mwm_api.get_clients(0))
    #mwm_api.cookie_jar = None
    #mwm_api.set_cookiejar_from_dict(cdict)
    #print(mwm_api.cookie_jar)
    # Get all SSID profiles
    #print(mwm_api.get_ssid_profiles())
    
    # Get managed devices
    print("\n\nGetting managed devices......")
    #mwm_api.cookie_jar = ""
    print(mwm_api.get_managed_ap_devices(0))

    # Fetch Location tree
    print("Fetching location tree.....")
    print(mwm_api.get_location_tree())
    tresult = mwm_api.get_client_conn_test_result(95)
    print(tresult)
    result_text = mwm_api.convert_conn_test_result_to_text(tresult)
    print(result_text)
    location = "corporate"
    print("\nFinding a location " + location + " by name....")
    locid = mwm_api.get_location_id_by_name(location)
    print("locid of location " + location+ " = " + str(locid))
    print("\nAP count = " + str(mwm_api.get_device_count_at_location(locid)))
    print("\nClient count = " + str(mwm_api.get_client_counts_at_loc(locid)))
    print("\nPerforming client conn test........")
    print(mwm_api.do_client_conn_test_at_loc(locid))
    print("\nClient count = " + str(mwm_api.get_client_counts_at_loc(locid)))
    # Logout from the service
    print("\nLogging out from API.......")
    mwm_api.logout()
    print("\nBye......")
