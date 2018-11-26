import os
from behaviour_handlers import BehaviourHandler
from behaviors import *
""" Events to invoke Lambda Function/Alexa skill"""

handler = BehaviourHandler()


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetPoints":
        return get_member_points(session)
    elif intent_name == "JokeIntent":
        return get_jokes(session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request(session)
    else:
        return unidentified_intent(session)


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


def handle_session_end_request(session):
    card_title = "Session Ended"
    session_end_response = "Thank you for using " + os.environ['CLIENT_DISPLAY_NAME'] + " " + os.environ["VIRTUAL_ASSISTANCE_EXPERIENCE"] +  \
                    ". Have a nice day! "
    
    speech_output = session_end_response
    
    if session['attributes']['InteractionBonusReceived']:
        speech_output = "Thank you for using " + os.environ['CLIENT_DISPLAY_NAME'] + " " + os.environ["VIRTUAL_ASSISTANCE_EXPERIENCE"] +  \
                        ". You received a total of 500 additional reward points for interacting with our Virtual Assistant Today.  Check back tomorrow for new rewards and promotions. Have a nice day! "

    session_end_speechlet = handler.build_speechlet_response(card_title=card_title,
                                                             speech_output=speech_output,
                                                             reprompt_text="",
                                                             should_end_session=True)

    session_end = handler.build_response(speechlet_response=session_end_speechlet, session_attributes=None)

    return session_end


def unidentified_intent(session):
    speech_output = "Sorry, I'm not sure.  Can you please repeat that? "

    unidentified_intent_speechlet = handler.build_speechlet_response(card_title="",
                                                                     speech_output=speech_output,
                                                                     reprompt_text="",
                                                                     should_end_session=False)

    unidentified_intent_response = handler.build_response(speechlet_response=unidentified_intent_speechlet,
                                                          session_attributes=session['attributes'])

    return unidentified_intent_response
