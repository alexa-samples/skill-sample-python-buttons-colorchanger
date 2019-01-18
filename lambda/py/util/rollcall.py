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
from . import animations, directives, settings
Colors = animations.Colors

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define some animations that we'll use during roll call, to be played in various situations,
# such as when buttons "check in" during roll call, or after both buttons were detected.
# See: https://developer.amazon.com/docs/gadget-skills/control-echo-buttons.html#animate
roll_call_complete_animation = animations.fade_in_animation(
    1, Colors.green, 5000)
button_check_in_idle_animation = animations.solid_animation(
    1, Colors.green, 8000)
button_check_in_down_animation = animations.solid_animation(
    1, Colors.green, 1000)
button_check_in_up_animation = animations.solid_animation(
    1, Colors.white, 4000)
timeout_animation = animations.fade_animation(1, Colors.black, 1000)

# Define two recognizers that will capture the first time each of two arbitrary buttons is pressed.
#  We'll use proxies to refer to the two different buttons because we don't know ahead of time
#  which two buttons will be used (see: https://developer.amazon.com/docs/gadget-skills/define-echo-button-events.html#proxies)
# The two recogniziers will be used as triggers for two input handler events, used during roll call.
# see: https://developer.amazon.com/docs/gadget-skills/define-echo-button-events.html#recognizers
roll_call_recognizers = {
    "roll_call_first_button_recognizer": PatternRecognizer(
        anchor=PatternRecognizerAnchorType.end,
        fuzzy=False,
        pattern=[Pattern(gadget_ids=["first_button"],
                         action=InputEventActionType.down)]
    ),
    "roll_call_second_button_recognizer": PatternRecognizer(
        anchor=PatternRecognizerAnchorType.end,
        fuzzy=True,
        pattern=[Pattern(gadget_ids=["first_button"], action=InputEventActionType.down), Pattern(
            gadget_ids=["second_button"], action=InputEventActionType.down)]
    )}

# Define named events based on the ROLL_CALL_RECOGNIZERS and the built-in "timed out" recognizer
# to report back to the skill when the first button checks in, when the second button checks in,
# as well as then the input handler times out, if this happens before two buttons checked in.
# see: https://developer.amazon.com/docs/gadget-skills/define-echo-button-events.html#define
roll_call_events = {
    "first_button_checked_in": Event(
        meets=["roll_call_first_button_recognizer"],
        reports=EventReportingType.matches,
        should_end_input_handler=False,
        maximum_invocations=1
    ),
    "second_button_checked_in": Event(
        meets=["roll_call_second_button_recognizer"],
        reports=EventReportingType.matches,
        should_end_input_handler=True,
        maximum_invocations=1
    ),
    "timeout": Event(
        meets=["timed out"],
        reports=EventReportingType.history,
        should_end_input_handler=True
    )
}

# ROLL_CALL_MODE Handlers
# set up handlers for events that are specific to the Roll Call mode


def new_session(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("rollcall.new_session: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    ctx["output_speech"] = ["Welcome to the Color Changer skill."]
    ctx["output_speech"].append(
        "This skill provides a brief introduction to the core")
    ctx["output_speech"].append(
        "functionality that every Echo Button skill should have.")
    ctx["output_speech"].append(
        "We'll cover roll call, starting and stopping the Input Handler,")
    ctx["output_speech"].append(
        "button events and Input Handler timeout events. ")
    ctx["output_speech"].append("Let's get started with roll call. ")
    ctx["output_speech"].append("Roll call wakes up the buttons to make sure")
    ctx["output_speech"].append("they're connected and ready for play. ")
    ctx["output_speech"].append(
        "Ok. Press the first button and wait for confirmation")
    ctx["output_speech"].append("before pressing the second button.")
    ctx["output_speech"].append(settings.WAITING_AUDIO)

    ctx["timeout"] = 50000

    return start_roll_call(handler_input)


def start_roll_call(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("rollcall.start_roll_call: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    ctx["directives"].append(
        StartInputHandlerDirective(
            timeout=ctx["timeout"],
            proxies=["first_button", "second_button"],
            recognizers=roll_call_recognizers,
            events=roll_call_events
        )
    )
    ctx["directives"].append(directives.button_down_animation_directive(
        button_check_in_down_animation))
    ctx["directives"].append(
        directives.button_up_animation_directive(button_check_in_up_animation))

    # start keeping track of some state
    # see: https://developer.amazon.com/docs/gadget-skills/save-state-echo-button-skill.html
    session_attributes["button_count"] = 0
    session_attributes["is_roll_call_complete"] = False
    session_attributes["expecting_skill_confirmation"] = False
    # setup an array of DeviceIDs to hold IDs of buttons that will be used in the skill
    session_attributes["device_ids"] = ["Device ID Listings"]
    # Save Start Input Request ID
    session_attributes["current_input_handler_id"] = handler_input.request_envelope.request.request_id

    ctx["open_microphone"] = False
    return handler_input.response_builder.response


def handle_first_button_check_in(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("rollcall.handle_first_button_check_in: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    # just in case we ever get this event, after the `second_button_checked_in` event
    # was already handled, we check the make sure the `buttonCount` attribute is set to 0;
    # if not, we will silently ignore the event
    if "button_count" in session_attributes and session_attributes["button_count"] == 0:
        # Say something when we first encounter a button
        ctx["output_speech"] = ["Hello, button 1."]
        ctx["output_speech"].append(settings.WAITING_AUDIO)

        first_button_id = ctx["game_input_events"][0].gadget_id
        ctx["directives"].append(directives.button_idle_animation_directive(
            button_check_in_idle_animation, [first_button_id]))

        session_attributes["device_ids"].append(first_button_id)
        session_attributes["button_count"] = 1

    ctx["open_microphone"] = False
    return handler_input.response_builder.response


def handle_second_button_check_in(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("rollcall.handle_second_button_check_in: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    ctx["reprompt"] = ["Please pick a color: green, red, or blue"]
    ctx["output_speech"] = []

    if "button_count" in session_attributes and session_attributes["button_count"] == 0:
        ctx["output_speech"].append("hello buttons 1 and 2")
        ctx["output_speech"].append("<break time='1s'/>")
        ctx["output_speech"].append("Awesome!")

        session_attributes["device_ids"].append(
            ctx["game_input_events"][0].gadget_id)
        session_attributes["device_ids"].append(
            ctx["game_input_events"][1].gadget_id)
    else:
        ctx["output_speech"].append("hello, button 2")
        ctx["output_speech"].append("<break time='1s'/>")
        ctx["output_speech"].append("Awesome. I've registered two buttons.")

        if ctx["game_input_events"][0].gadget_id in session_attributes["device_ids"]:
            session_attributes["device_ids"].append(
                ctx["game_input_events"][1].gadget_id)
        else:
            session_attributes["device_ids"].append(
                ctx["game_input_events"][0].gadget_id)

    session_attributes["button_count"] = 2

    # .. and ask use to pick a color for the next stage of the skill
    ctx["output_speech"].append("Now let's learn about button events.")
    ctx["output_speech"].append(
        "Please select one of the following colors: red, blue, or green.")

    device_ids = session_attributes["device_ids"][1:]

    # send an idle animation to registered buttons
    ctx["directives"].append(directives.button_idle_animation_directive(
        roll_call_complete_animation, device_ids))
    # reset button press animations until the user chooses a color
    ctx["directives"].append(directives.button_up_animation_directive(
        settings.DEFAULT_ANIMATION_BUTTON_UP, device_ids))
    ctx["directives"].append(directives.button_down_animation_directive(
        settings.DEFAULT_ANIMATION_BUTTON_DOWN, device_ids))

    session_attributes["is_roll_call_complete"] = True
    session_attributes["state"] = settings.SKILL_STATES["PLAY_MODE"]

    ctx["open_microphone"] = True
    return handler_input.response_builder.response


def handle_timeout(handler_input):
    # type: (HandlerInput) -> Response
    logger.info("rollcall.handle_timeout: handling request")

    ctx = handler_input.attributes_manager.request_attributes
    session_attributes = handler_input.attributes_manager.session_attributes

    ctx["output_speech"] = ["For this skill we need two buttons."]
    ctx["output_speech"].append(
        "Would you like more time to press the buttons?")
    ctx["reprompt"] = ["Say yes to go back and add buttons, or no to exit now."]

    device_ids = session_attributes["device_ids"][1:]

    # send an idle animation for timeout
    ctx["directives"].append(
        directives.button_idle_animation_directive(timeout_animation, device_ids))
    # reset button press animations
    ctx["directives"].append(directives.button_up_animation_directive(
        settings.DEFAULT_ANIMATION_BUTTON_UP, device_ids))
    ctx["directives"].append(directives.button_down_animation_directive(
        settings.DEFAULT_ANIMATION_BUTTON_DOWN, device_ids))

    ctx["open_microphone"] = True
    session_attributes["expecting_end_skill_confirmation"] = True
    return handler_input.response_builder.response
