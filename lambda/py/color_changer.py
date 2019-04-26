"""
    Copyright 2018 Amazon.com, Inc. and its affiliates. All Rights Reserved.
    Licensed under the Amazon Software License (the "License").
    You may not use this file except in compliance with the License.
    A copy of the License is located at

      http://aws.amazon.com/asl/

    or in the "license" file accompanying this file. This file is distributed
    on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express
    or implied. See the License for the specific language governing
    permissions and limitations under the License.
"""
import logging
import json

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.serialize import DefaultSerializer

from ask_sdk_model import Response, SessionEndedRequest
from ask_sdk_model.interfaces.gadget_controller import SetLightDirective
from ask_sdk_model.interfaces.game_engine import (
    StartInputHandlerDirective, StopInputHandlerDirective)
from ask_sdk_model.services.game_engine import (
    Event, EventReportingType, PatternRecognizer, PatternRecognizerAnchorType,
    Pattern, InputEventActionType, InputEvent
)
from ask_sdk_model.services.gadget_controller import (
    AnimationStep, LightAnimation, SetLightParameters, TriggerEventType
)

from util import rollcall, game, settings, directives

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

serializer = DefaultSerializer()

sb = SkillBuilder()


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.launch_request_handler: handling request")

    return rollcall.new_session(handler_input)


@sb.exception_handler(can_handle_func=lambda i, e: True)
def error_handler(handler_input, exception):
    """Exception Handler"""
    # type: (HandlerInput) -> Response
    logger.info("error_handler: handling request")
    logger.error(exception, exc_info=True)

    speech = "Sorry, there was some problem. Please try again later!!"
    handler_input.response_builder.set_should_end_session(True)
    handler_input.response_builder.speak(speech)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.help_intent_handler: handling request")
    help_response(handler_input)


def help_response(handler_input):
    """Help Message"""
    # type: (HandlerInput) -> Response
    logger.info("help_response")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    if "current_input_handler_id" in session_attributes:
        # if there is an active input handler, stop it so it doesn't interrup Alexa speaking the Help prompt
        # see: https://developer.amazon.com/docs/echo-button-skills/receive-echo-button-events.html#stop
        ctx["directives"].append(
            StopInputHandlerDirective(
                originating_request_id=session_attributes["current_input_handler_id"]
            )
        )

    if "is_roll_call_complete" in session_attributes and session_attributes["is_roll_call_complete"]:
        ctx["output_speech"] = ["Now that you have registered two buttons, "]
        ctx["output_speech"].append(
            "you can pick a color to show when the buttons are pressed. ")
        ctx["output_speech"].append(
            "Select one of the following colors: red, blue, or green. ")
        ctx["output_speech"].append(
            "If you do not wish to continue, you can say exit. ")
        ctx["reprompt"] = ["Pick a color to test your buttons: red, blue, or green. "]
        ctx["reprompt"].append(" Or say cancel or exit to quit. ")
    else:
        ctx["output_speech"] = [
            "You will need two Echo buttons to to use this skill. "]
        ctx["output_speech"].append("Each of the two buttons you plan to use ")
        ctx["output_speech"].append(
            "must be pressed for the skill to register them. ")
        ctx["output_speech"].append(
            "Would you like to continue and register two Echo buttons? ")
        ctx["reprompt"] = ["You can say yes to continue, or no or exit to quit."]
        session_attributes["expecting_skill_confirmation"] = True

    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda handler_input:
        is_intent_name("AMAZON.CancelIntent")(handler_input) or
        is_intent_name("AMAZON.StopIntent")(handler_input))
def stop_and_cancel_intent_handler(handler_input):
    """Single handler for Stop and Cancel Intent."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.stop_and_cancel_intent_handler: handling request")
    return stop_response(handler_input)


def stop_response(handler_input):
    """Stop or cancel response."""
    # type: (HandlerInput) -> Response
    logger.info("stop_response")

    ctx = handler_input.attributes_manager.request_attributes
    ctx["output_speech"] = ["Good Bye!"]

    return end_session(handler_input)


@sb.request_handler(can_handle_func=is_request_type("GameEngine.InputHandlerEvent"))
def game_engine_input_handler(handler_input):
    """Handler for all game engine events."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.game_engine_input_handler: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes
    request = handler_input.request_envelope.request

    if ("current_input_handler_id" in session_attributes
            and request.originating_request_id != session_attributes["current_input_handler_id"]):
        logger.warn("Stale input received -> received event from " + request.originating_request_id +
                    "(was expecting " + session_attributes["current_input_handler_id"] + ")")
        ctx["open_microphone"] = False
        return handler_input.response_builder.response

    game_engine_events = request.events if request.events else []
    for evt in game_engine_events:
        # In this request type, we'll see one or more incoming events
        # that correspond to the StartInputHandler we sent above.
        if evt.name == "first_button_checked_in":
            ctx["game_input_events"] = evt.input_events
            return rollcall.handle_first_button_check_in(handler_input)
        elif evt.name == "second_button_checked_in":
            ctx["game_input_events"] = evt.input_events
            return rollcall.handle_second_button_check_in(handler_input)
        elif evt.name == "button_down_event":
            if session_attributes["state"] == settings.SKILL_STATES["PLAY_MODE"]:
                ctx["game_input_events"] = evt.input_events
                return game.handle_button_pressed(handler_input)
        elif evt.name == "timeout":
            if session_attributes["state"] == settings.SKILL_STATES["PLAY_MODE"]:
                ctx["game_input_events"] = evt.input_events
                return game.handle_timeout(handler_input)
            else:
                return rollcall.handle_timeout(handler_input)

    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.YesIntent"))
def yes_handler(handler_input):
    """Handler for all other unhandled requests."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.yes_handler: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    if (session_attributes["state"] == settings.SKILL_STATES["ROLL_CALL_MODE"]
        and "expecting_end_skill_confirmation" in session_attributes
            and session_attributes["expecting_end_skill_confirmation"]):
        ctx["output_speech"] = [
            "Ok. Press the first button, wait for confirmation,"]
        ctx["output_speech"].append("then press the second button.")
        ctx["output_speech"].append(settings.WAITING_AUDIO)
        ctx["timeout"] = 30000
        return rollcall.start_roll_call(handler_input)
    elif session_attributes["state"] == settings.SKILL_STATES["EXIT_MODE"]:
        if ("expecting_end_skill_confirmation" in session_attributes
                and session_attributes["expecting_end_skill_confirmation"]):

            return end_session(handler_input)
        else:
            return catch_all(handler_input)
    else:
        return help_response(handler_input)


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.NoIntent"))
def no_handler(handler_input):
    """Handler for all other unhandled requests."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.no_handler: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    if (session_attributes["state"] == settings.SKILL_STATES["ROLL_CALL_MODE"]
        and "expecting_end_skill_confirmation" in session_attributes
            and session_attributes["expecting_end_skill_confirmation"]):
        return stop_response(handler_input)
    elif session_attributes["state"] == settings.SKILL_STATES["EXIT_MODE"]:
        if ("expecting_end_skill_confirmation" in session_attributes
                and session_attributes["expecting_end_skill_confirmation"]):
            ctx["reprompt"] = ["Pick a different color, red, blue, or green."]
            ctx["output_speech"] = ["Ok, let's keep going."]
            ctx["output_speech"].append(ctx["reprompt"][0])
            ctx["open_microphone"] = True
            session_attributes["state"] = settings.SKILL_STATES["PLAY_MODE"]
            return handler_input.response_builder.response
        else:
            return catch_all(handler_input)
    else:
        return help_response(handler_input)


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    logger.info("session_ended_request_handler: handling request")
    return end_session(handler_input)


def end_session(handler_input):
    """Session End."""
    # type: (HandlerInput) -> Response
    logger.info("end_session")

    request = handler_input.request_envelope.request
    if isinstance(request, SessionEndedRequest):
        if request.reason is not None:
            logger.info("Session ended with reason: " +
                        request.reason.to_str())
        if request.error is not None:
            logger.info("Session ended with error: " + request.error.to_str())

    ctx = handler_input.attributes_manager.request_attributes
    ctx["output_speech"] = ["Good bye!"]
    handler_input.response_builder.set_should_end_session(True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input: True)
def default_handler(handler_input):
    """Handler for all other unhandled requests."""
    # type: (HandlerInput) -> Response
    logger.info("color_changer.default_handler: handling request")
    return catch_all(handler_input)


def catch_all(handler_input):
    """Handle anything that falls through the cracks"""
    # type: (HandlerInput) -> Response
    logger.info("catch_all")
    if is_intent_name("colorIntent"):
        return game.color_intent_handler(handler_input)

    ctx = handler_input.attributes_manager.request_attributes
    ctx["reprompt"] = ["Please say again, or say help if you're not sure what to do."]
    ctx["output_speech"] = ["Sorry, I didn't get that. " + ctx["reprompt"][0]]
    ctx["open_microphone"] = True

    return handler_input.response_builder.response


@sb.global_request_interceptor()
def request_interceptor(handler_input):
    """Request Interceptor"""
    # type: (HandlerInput) -> None
    logger.info("==Request==")
    serialized = serializer.serialize(handler_input.request_envelope)
    logger.info(json.dumps(serialized, indent=4))
    logger.info("==Session Attributes==")
    logger.info(json.dumps(
        handler_input.attributes_manager.session_attributes, indent=4))

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    # Assign ROLL_CALL_MODE if we don't have a state
    if "state" not in session_attributes or session_attributes["state"] is None:
        session_attributes["state"] = settings.SKILL_STATES["ROLL_CALL_MODE"]

    ctx["output_speech"] = []
    ctx["directives"] = []
    ctx["reprompt"] = []


@sb.global_response_interceptor()
def response_interceptor(handler_input, response):
    """Response Interceptor."""
    # type: (HandlerInput, Response) -> None

    ctx = handler_input.attributes_manager.request_attributes
    response_builder = handler_input.response_builder

    if len(ctx["output_speech"]) > 0:
        logger.info(
            "Adding " + str(len(ctx["output_speech"])) + " speech parts.")
        speech_text = " ".join(ctx["output_speech"])
        response_builder.speak(speech_text)

    if len(ctx["reprompt"]) > 0:
        logger.info("Adding " + str(len(ctx["reprompt"])) + " reprompt parts.")
        reprompt = " ".join(ctx["reprompt"])
        response_builder.ask(reprompt)

    if "open_microphone" in ctx:
        if ctx["open_microphone"]:
            # setting shouldEndSession = fase  -  lets Alexa know that we want an answer from the user
            # see: https://developer.amazon.com/docs/echo-button-skills/receive-voice-input.html#open
            # https://developer.amazon.com/docs/echo-button-skills/keep-session-open.html
            response_builder.set_should_end_session(False)
        else:
            # deleting shouldEndSession will keep the skill session going,
            # while the input handler is active, waiting for button presses
            # see: https://developer.amazon.com/docs/echo-button-skills/keep-session-open.html
            response_builder.set_should_end_session(None)

    logger.info("Adding " + str(len(ctx["directives"])) + " directives")
    for directive in ctx["directives"]:
        response_builder.add_directive(directive)

    logger.info("==Response==")
    serialized = serializer.serialize(response)
    logger.info(json.dumps(serialized, indent=4))
    logger.info("==Session Attributes==")
    logger.info(json.dumps(
        handler_input.attributes_manager.session_attributes, indent=4))

    return response_builder.response


handler = sb.lambda_handler()
