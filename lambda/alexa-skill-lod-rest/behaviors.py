""" Various functions to return data based on the intent"""
from client_service_requests import make_loyalty_get_request, make_loyalty_post_request, get_access_token
from behaviour_handlers import BehaviourHandler
import os
import random


handler = BehaviourHandler()


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    client_service_access_token = get_access_token()

    get_member_url = '{}/api/v1/loyalty/members/{}/'.format(os.environ['CLIENT_SERVICE_URL'], os.environ['MEMBER_ID'])
    client_service_member_data = make_loyalty_get_request(get_member_url, client_service_access_token)
    
    get_member_points_url = '{}/api/v1/loyalty/members/{}/accountSummary'.format(os.environ['CLIENT_SERVICE_URL'],
                                                                                 os.environ['MEMBER_ID'])
    member_points_data = make_loyalty_get_request(get_member_points_url, client_service_access_token)
    member_points_value = int(float(member_points_data['currencyBalance']))
    interaction_bonus_received = set_alexa_interaction_bonus(client_service_access_token)

    session_attributes = {"ClientServiceAuthorizationToken": client_service_access_token,
                          "MemberData": client_service_member_data,
                          "MemberStartingPointBalance": member_points_value,
                          "InteractionBonusReceived": interaction_bonus_received,
                          }

    speech_output = "Hello {}, Welcome to {} {} Service." \
                    " Try saying, check my points balance.".format(client_service_member_data['firstName'],
                                                         os.environ["CLIENT_DISPLAY_NAME"],
                                                         os.environ["VIRTUAL_ASSISTANCE_EXPERIENCE"])

    reprompt_text = "Please ask me, " \
                    "What is my current point balance."

    welcome_response_speechlet = handler.build_speechlet_response(card_title=os.environ["VIRTUAL_ASSISTANCE_EXPERIENCE"],
                                                                  speech_output=speech_output,
                                                                  reprompt_text=reprompt_text,
                                                                  should_end_session=False)

    welcome_response = handler.build_response(speechlet_response=welcome_response_speechlet,
                                              session_attributes=session_attributes)

    return welcome_response


def set_alexa_interaction_bonus(client_service_access_token):
    """Get Alexa Interaction Bonus"""
    get_member_activity_url = '{}/api/v1/loyalty/members/{}/accountActivity'.format(os.environ['CLIENT_SERVICE_URL'],
                                                                                 os.environ['MEMBER_ID'])
    member_activity_data = make_loyalty_get_request(get_member_activity_url, client_service_access_token)
    
    print(member_activity_data)
    interaction_bonus_received = False
    if member_activity_data is not None:
        for activity in member_activity_data:
            print(activity)
            if activity['pointEvent'] == "AlexaEvent":
                interaction_bonus_received = True
    
    return interaction_bonus_received
                

def get_member_points(session):
    """Get back customer points"""
    get_member_points_url = '{}/api/v1/loyalty/members/{}/accountSummary'.format(os.environ['CLIENT_SERVICE_URL'],
                                                                                 os.environ['MEMBER_ID'])
    member_points_data = make_loyalty_get_request(get_member_points_url, session['attributes']['ClientServiceAuthorizationToken'])
    member_points_value = int(float(member_points_data['currencyBalance']))

    card_title = "Point Balance"

    speech_output = "{},  Your current point balance is {} points. ".format(
        session['attributes']['MemberData']['firstName'],
        member_points_value)

    reprompt_text = "Please say, " \
                    "What is my current point balance. To check your {} points balance".format(os.environ[
                        'CLIENT_DISPLAY_NAME'])

    get_member_points_speechlet = handler.build_speechlet_response(card_title=card_title,
                                                                   speech_output=speech_output,
                                                                   reprompt_text=reprompt_text,
                                                                   should_end_session=False)

    member_points_response = handler.build_response(speechlet_response=get_member_points_speechlet,
                                                    session_attributes=session['attributes'])

    return member_points_response


def add_interaction_bonus(session):
    """Get member bonus"""

    member_bonus_url = '{}/api/v1/loyalty/members/{}/triggerEvent?eventName={}'.format(os.environ['CLIENT_SERVICE_URL'],
                                                                                       os.environ['MEMBER_ID'],
                                                                                       os.environ['MEMBER_EVENT'])
    member_bonus_data = make_loyalty_post_request(member_bonus_url, session['attributes']['ClientServiceAuthorizationToken'])

    if member_bonus_data is None:
        session['attributes']['InteractionBonusReceived'] = True
        return True
    else:
        return False


def get_jokes(session):
    """ Get a random joke and then award the user for interaction once per time period."""

    card_title = "{} telling jokes.".format(os.environ['VIRTUAL_ASSISTANCE_EXPERIENCE'])

    jokes = ["What do you call an alligator in a vest?   An investa gator!",
             "Why do golfers wear two pairs of pants?   Just in case they get a hole in one.",
             "What’s the difference between a well-dressed man and a tired dog?   One wears a suit; the other just pants.",
             "What do lawyers wear to formal dinners?   Lawsuits!",
             "Why did the leopard wear a striped shirt?  So, she wouldn't be spotted!"]
    joke = random.choice(jokes)
    speech_output = joke
    
    #if abs(member_points_value - int(float(session['attributes']['MemberStartingPointBalance']))) == 0:
    #if not "pointEvent" in member_activity_data and member_activity_data["pointEvent"] == "DPPoints":
    if not session['attributes']['InteractionBonusReceived']:
        if add_interaction_bonus(session):
            speech_output = "{} You've just received {} additional rewards points for being awesome!".format(joke,"500")

    reprompt_text = "Did you want me to make you laugh? " \
                    "Say Tell me a joke."

    get_joke_speechlet = handler.build_speechlet_response(card_title=card_title,
                                                          speech_output=speech_output,
                                                          reprompt_text=reprompt_text,
                                                          should_end_session=False)

    get_joke_response = handler.build_response(speechlet_response=get_joke_speechlet,
                                               session_attributes=session['attributes'])

    return get_joke_response

