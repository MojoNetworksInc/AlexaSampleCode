
from __future__ import print_function

from mwmApi import MwmApi
# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(output, reprompt_text, should_end_session, directives):
    resp = {}
    if output != None:
        resp['outputSpeech'] = {
            'type': 'PlainText',
            'text': output
        }
    if reprompt_text != None:
        resp['reprompt'] = {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        }
    resp['shouldEndSession'] = should_end_session
    if directives != None:
        resp['directives'] = directives

    return resp

def build_response(session_attributes, speechlet_response):
    resp = {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
    print("Returning resp: ")
    print(resp)
    return resp

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response(session):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    session_attributes = {}
    mwm_api = get_mwm_api(session)
    if mwm_api is not None:
        session_attributes['cookiejar_dict'] = mwm_api.get_cookiejar_dict()

    card_title = "Welcome"
    speech_output = "Hello, welcome to mojo aware. What can I do?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "You can ask me for network status at a location or perform a live network test. Please go ahead. "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        speech_output, reprompt_text, should_end_session, None))

def get_delegate_directive():
        return [{"type":"Dialog.Delegate"}]

def handle_session_end_request(session):
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    close_mwm_api(session)
    return build_response({}, build_speechlet_response(
        speech_output, None, should_end_session, None))

def get_network_status_speech_output(ap_count, client_count, location):
    rv = "Unable to get network status at location " + location + ". Please try again"

    if not isinstance(ap_count, dict) or not isinstance(client_count, dict):
        return rv
    if "active" not in ap_count or "inactive" not in ap_count:
        return rv
    if "successCount" not in client_count or "failureCount" not in client_count:
        return rv

    active_aps = ap_count['active']
    inactive_aps = ap_count['inactive']
    cl_succ = client_count['successCount']
    cl_fail = client_count['failureCount']

    rv = "Network status for location " + location + " is as follows. "
    rv = rv + "There are " + str(active_aps) + " active Access Points and " + str(inactive_aps) + " inactive Access Points. "
    rv = rv + str(cl_succ) + " clients have successfully connected to the network and " + str(cl_fail) + " clients have failed to connect to the network."

    return rv


def get_network_status(dialogState, intent, session):

    card_title = intent['name']
    session_attributes = {}
    mwm_api = get_mwm_api(session)
    if mwm_api is not None:
        session_attributes['cookiejar_dict'] = mwm_api.get_cookiejar_dict()
    should_end_session = False
    print("dialogState: " + str(dialogState))
    if dialogState != None and dialogState != "COMPLETED":
        print("Dialog state is not yet complete, returning Dialog.Delegate...")
        resp = build_response(session_attributes, build_speechlet_response(
            None, None, should_end_session, get_delegate_directive()))
        print(resp)
        return resp

    if 'location' in intent['slots'] and intent['slots']['location']['value'] != None:
        location = intent['slots']['location']['value']
        locid = mwm_api.get_location_id_by_name(location)
        ap_count = 0
        client_count = 0
        if locid != -2:
            session_attributes['location'] = location
            ap_count = mwm_api.get_device_count_at_location(locid)
            client_count = mwm_api.get_client_counts_at_loc(locid)
            speech_output = get_network_status_speech_output(ap_count, client_count, location)
            reprompt_text = "You can ask me for network status at a location or perform a live network test. Please go ahead. "
        else:
            speech_output = "Could not find location named " + location +". Please try again with a valid location name"
        
            reprompt_text = "You can ask me for network status at a location or perform a live network test. Please go ahead. "
    else:
        speech_output = "Please try again by specifying a valid location name"
        reprompt_text = "You can ask me for network status at a location or perform a live network test. Please go ahead. "

    return build_response(session_attributes, build_speechlet_response(
        speech_output, reprompt_text, should_end_session, None))


def get_result_of_last_successful_test(dialogState, intent, session):
    session_attributes = {}
    should_end_session = False
    mwm_api = get_mwm_api(session)
    if mwm_api is not None:
        session_attributes['cookiejar_dict'] = mwm_api.get_cookiejar_dict()
    reprompt_text = None
    print("dialogState: " + str(dialogState))
    if dialogState != None and dialogState != "COMPLETED":
        print("Dialog state is not yet complete, returning Dialog.Delegate...")
        resp = build_response(session_attributes, build_speechlet_response(
            None, None, should_end_session, get_delegate_directive()))
        print(resp)
        return resp

    tresult = mwm_api.get_client_conn_test_result(95)
    print(tresult)
    result_text = mwm_api.convert_conn_test_result_to_text(tresult)
    if result_text != None:
        speech_output = "Result of last successful test is as follows. " + result_text
    else:
        speech_output = "Unable to fetch the result of last successful test. Please try again"
    
    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        speech_output, reprompt_text, should_end_session, None))

def perform_client_test(dialogState, intent, session):
    session_attributes = {}
    should_end_session = False
    mwm_api = get_mwm_api(session)
    if mwm_api is not None:
        session_attributes['cookiejar_dict'] = mwm_api.get_cookiejar_dict()
    reprompt_text = None
    print("dialogState: " + str(dialogState))
    if dialogState != None and dialogState != "COMPLETED":
        print("Dialog state is not yet complete, returning Dialog.Delegate...")
        resp = build_response(session_attributes, build_speechlet_response(
            None, None, should_end_session, get_delegate_directive()))
        print(resp)
        return resp

    if 'location' in intent['slots'] and intent['slots']['location']['value'] != None:
        location = intent['slots']['location']['value']
        locid = mwm_api.get_location_id_by_name(location)
        if locid != -2:
            resp = mwm_api.do_client_conn_test_at_loc(locid)
            if resp['rv'] != 0:
                speech_output = "Could not perform client connectivity test at location " + location + " due to error: '" + resp['error_string'] + "."
            else:
                speech_output = "Network test complete. Here are the results. " + resp['result_text']
        else:
            speech_output = "Could not find location named " + location +". Please try again with a valid location name"
    else:
        speech_output = "Please try again by specifying a valid location name"
    
    
    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        speech_output, reprompt_text, should_end_session, None))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])
          
def create_mwm_api(cookiejar_dict):
    host = "alpha-mwm.mojonetworks.com"
    #host = dashboard-l3stagingblr.dt.airtightnw.com
    mwm_api = MwmApi(host, None)

    # Login to MWM using KVS
    client = "api-client"
    login_timeout = "3000"
    #kvs_auth_data = {
    #    "keyId": "KEY-ATN14-20",
    #    "keyValue": "850151c6cc4860e123455853d6ebc811",
    #    "cname": "ATN19",
    #}
    kvs_auth_data = {
        "keyId": "KEY-ATN8-02", # This keyId is invalid, replace it by your KeyId
        "keyValue": "0abc2f8664b123450ebc406276929320", # This keyValue is invalid, replace it with your keyValue
        "cname": "ATN9" # Replace this with you cname
    }

    if cookiejar_dict is None:
        print("Cookiejar is empty. Calling login method...")
        mwm_api.login(client, login_timeout, kvs_auth_data)
    else:
        print("Cookiejar exists. Setting it...")
        mwm_api.set_cookiejar_from_dict(cookiejar_dict)
    return mwm_api

def get_mwm_api(session):
    cookiejar_dict = None
    
    if  "cookiejar_dict" in session.get('attributes', {}):
        cookiejar_dict = session['attributes']['cookiejar_dict']

    return create_mwm_api(cookiejar_dict)    
    
def close_mwm_api(session):
    mwm_api = get_mwm_api(session)
    if mwm_api is not None:
        mwm_api.logout()

def good_bye_msg(dialogState, intent, session):
    close_mwm_api(session)
    speech_output = "You are welcome. I love Mojo Cognitive Cloud WiFi. Good Bye.."
    return build_response({}, build_speechlet_response(
        speech_output, None, True, None))

def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response(session)


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    print(intent_request)
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']
 
    dialogState = None
    if "dialogState" in intent_request:
        dialogState = intent_request['dialogState']

    # Dispatch to your skill's intent handlers
    if intent_name == "NetworkStatus":
        return get_network_status(dialogState, intent, session)
    elif intent_name == "GoodBye":
        return good_bye_msg(dialogState, intent, session)
    elif intent_name == "ClientTest":
        return perform_client_test(dialogState, intent, session)
    elif intent_name == "LiveNetworkTest":
        return perform_client_test(dialogState, intent, session)
    elif intent_name == "LastSuccessfulTest":
        return get_result_of_last_successful_test(dialogState, intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response(session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request(session)
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    close_mwm_api(session)
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

