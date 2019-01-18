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

    Gadgets Test Skill opens with buttons roll call and asks the user to
    push two buttons. On button one press, she changes the color to red and on
    button two press she changes the color to blue. Then closes. This Skill
    demonstrates how to send directives to, and receive events from, Echo Buttons.
"""
from ask_sdk_model.interfaces.gadget_controller import SetLightDirective
from ask_sdk_model.interfaces.game_engine import (
    StartInputHandlerDirective, StopInputHandlerDirective
)
from ask_sdk_model.services.gadget_controller import (
    SetLightParameters, TriggerEventType
)


def button_idle_animation_directive(animation, target_gadgets=[]):
    """ returns a SetLight directive, with a 'none' trigger, that can be added to an Alexa skill response """
    return SetLightDirective(
        version=1,
        target_gadgets=target_gadgets,
        parameters=SetLightParameters(
            trigger_event=TriggerEventType.none,
            trigger_event_time_ms=0,
            animations=[animation]
        )
    )


def button_up_animation_directive(animation, target_gadgets=[]):
    """ returns a SetLight directive, with a 'buttonUp' trigger, that can be added to an Alexa skill response """
    return SetLightDirective(
        version=1,
        target_gadgets=target_gadgets,
        parameters=SetLightParameters(
            trigger_event=TriggerEventType.buttonUp,
            trigger_event_time_ms=0,
            animations=[animation]
        )
    )


def button_down_animation_directive(animation, target_gadgets=[]):
    """ returns a SetLight directive, with a 'buttonDown' trigger, that can be added to an Alexa skill response """
    return SetLightDirective(
        version=1,
        target_gadgets=target_gadgets,
        parameters=SetLightParameters(
            trigger_event=TriggerEventType.buttonDown,
            trigger_event_time_ms=0,
            animations=[animation]
        )
    )
