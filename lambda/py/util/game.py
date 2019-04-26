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
from ask_sdk_model.services.game_engine import (
    Event, EventReportingType, PatternRecognizer, PatternRecognizerAnchorType,
    Pattern, InputEventActionType, InputEvent
)
from ask_sdk_model.interfaces.game_engine import StartInputHandlerDirective
from . import animations, directives
from . import animations, directives, settings
Colors = animations.Colors

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define a recognizer for button down events that will match when any button is pressed down.
# We'll use this recognizer as trigger source for the "button_down_event" during play
# see: https://developer.amazon.com/docs/echo-button-skills/define-echo-button-events.html#recognizers
button_down_recognizer = {
    "button_down_recognizer": PatternRecognizer(
        anchor=PatternRecognizerAnchorType.end,
        fuzzy=False,
        pattern=[{"action": InputEventActionType.down}]
    )
}

# Define named events based on the DIRECT_BUTTON_DOWN_RECOGNIZER and the built-in "timed out" recognizer
# to report back to the skill when either of the two buttons in play was pressed and eventually when the
# input handler times out
# see: https://developer.amazon.com/docs/echo-button-skills/define-echo-button-events.html#define
game_events = {
    "button_down_event": Event(
        meets=["button_down_recognizer"],
        reports=EventReportingType.matches,
        should_end_input_handler=False
    ),
    "timeout": Event(
        meets=["timed out"],
        reports=EventReportingType.history,
        should_end_input_handler=True
    )
}

# PLAY_MODE Handlers
# set up handlers for events that are specific to the Play mode
# after the user registered the buttons - this is the main mode


def color_intent_handler(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("game.color_intent_handler: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes
    request_envelope = handler_input.request_envelope

    slots = handler_input.request_envelope.request.intent.slots
    user_color = None
    if "color" in slots:
        user_color = slots["color"].value
    logger.info("User selected color: " + str(user_color))

    if user_color != None and user_color in settings.COLORS_ALLOWED:
        session_attributes["user_color"] = user_color

        # Build Start Input Handler Directive
        ctx["directives"].append(
            StartInputHandlerDirective(
                timeout=30000,
                proxies=None,
                recognizers=button_down_recognizer,
                events=game_events
            )
        )

        # Save Input Handler Request ID
        session_attributes["current_input_handler_id"] = request_envelope.request.request_id

        device_ids = session_attributes["device_ids"][1:]

        # Build 'idle' breathing animation, based on the users color of choice, that will play immediately
        color = Colors.get_color(user_color)
        logger.info("Derived color is: " + str(color))
        animation_color = settings.BREATH_COLORS.get(color)
        ctx["directives"].append(directives.button_idle_animation_directive(
            animations.breathe_animation(30, animation_color, 450), device_ids))

        # Build 'button down' animation, based on the users color of choice, for when the button is pressed
        ctx["directives"].append(directives.button_down_animation_directive(
            animations.solid_animation(1, color, 2000), device_ids))

        # build 'button up' animation, based on the users color of choice, for when the button is released
        ctx["directives"].append(directives.button_up_animation_directive(
            animations.solid_animation(1, color, 200), device_ids))

        ctx["output_speech"] = ["Ok. " + user_color + " it is."]
        ctx["output_speech"].append(
            "When you press a button, it will now turn " + user_color + ".")
        ctx["output_speech"].append(
            "Pressing the button will also interrupt me if I'm speaking")
        ctx["output_speech"].append(
            "or playing music. I'll keep talking so you can interrupt me.")
        ctx["output_speech"].append("Go ahead and try it.")
        ctx["output_speech"].append(settings.WAITING_AUDIO)

        ctx["open_microphone"] = True
    else:
        ctx["reprompt"] = ["What color was that? Please pick a valid color!"]
        ctx["output_speech"] = ["Sorry, I didn't get that. " + ctx["reprompt"][0]]
        ctx["open_microphone"] = True

    return handler_input.response_builder.response


def handle_timeout(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("game.handle_timeout: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    ctx["output_speech"] = ["The input handler has timed out."]
    ctx["output_speech"].append(
        "That concludes our test, would you like to quit?")
    ctx["reprompt"] = ["Would you like to exit?"]
    ctx["reprompt"].append("Say Yes to exit, or No to keep going")

    user_color = session_attributes["user_color"]
    color = Colors.get_color(user_color)
    device_ids = session_attributes["device_ids"][1:]

    ctx["directives"].append(directives.button_idle_animation_directive(
        animations.fade_out_animation(1, color, 2000), device_ids))
    ctx["directives"].append(directives.button_down_animation_directive(
        settings.DEFAULT_ANIMATION_BUTTON_DOWN, device_ids))
    ctx["directives"].append(directives.button_up_animation_directive(
        settings.DEFAULT_ANIMATION_BUTTON_UP, device_ids))

    session_attributes["expecting_end_skill_confirmation"] = True
    session_attributes["state"] = settings.SKILL_STATES["EXIT_MODE"]
    ctx["open_microphone"] = True

    return handler_input.response_builder.response


def handle_button_pressed(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("game.handle_button_pressed: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    device_ids = session_attributes["device_ids"]
    game_inputs = ctx["game_input_events"]
    button_id = game_inputs[0].gadget_id

    if button_id in device_ids:
        button_index = device_ids.index(button_id)
        ctx["output_speech"] = ["Button " + str(button_index) + ". "]
        ctx["output_speech"].append(settings.WAITING_AUDIO)
    else:
        ctx["output_speech"] = ["Unregistered button"]
        ctx["output_speech"].append(
            "Only buttons registered during roll call are in play.")
        ctx["output_speech"].append(settings.WAITING_AUDIO)

    ctx["open_microphone"] = False
    return handler_input.response_builder.response
