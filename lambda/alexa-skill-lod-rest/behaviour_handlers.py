import os


class BehaviourHandler:

    def build_speechlet_response(self, card_title, speech_output, reprompt_text, should_end_session):
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': speech_output
            },
            'card': {
                'type': 'Simple',
                'title': os.environ['CLIENT_DISPLAY_NAME'] + " - " + card_title,
                'content': os.environ['CLIENT_DISPLAY_NAME'] + " - " + speech_output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }

    def build_response(self, session_attributes, speechlet_response):
        return {
            'version': '1.0',
            'sessionAttributes': session_attributes,
            'response': speechlet_response
        }
