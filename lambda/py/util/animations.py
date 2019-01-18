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
import logging
from enum import Enum
from ask_sdk_model.services.gadget_controller import (
    AnimationStep, LightAnimation)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Colors(Enum):
    white = "ffffff"
    red = "ff0000"
    light_red = "603018"
    orange = "ff3300"
    green = "00ff00"
    light_green = "184518"
    blue = "0000ff"
    light_blue = "184066"
    purple = "4b0098"
    yellow = "ffd400"
    black = "000000"

    @classmethod
    def get_color(cls, color_string):
        try:
            return cls[color_string.lower()]
        except KeyError:
            logger.warn("UNKNOWN COLOR: {0}".format(color_string))
            # Default to black - aka off - rather than raise the exception
            return cls.black


def solid_animation(cycles, color, duration):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=duration,
                blend=False,
                color=color.value
            )
        ]
    )


def fade_animation(cycles, color, duration):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=duration,
                blend=True,
                color=color.value
            )
        ]
    )


def fade_in_animation(cycles, color, duration):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=1,
                blend=True,
                color=Colors.black.value
            ),
            AnimationStep(
                duration_ms=duration,
                blend=False,
                color=color.value
            )
        ]
    )


def fade_out_animation(cycles, color, duration):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=duration,
                blend=True,
                color=color.value
            ),
            AnimationStep(
                duration_ms=1,
                blend=True,
                color=Colors.black.value
            )
        ]
    )


def cross_fade_animation(cycles, color_one, color_two, duration_one, duration_two):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=duration_one,
                blend=True,
                color=color_one.value
            ),
            AnimationStep(
                duration_ms=duration_two,
                blend=True,
                color=color_two.value
            )
        ]
    )


def breathe_animation(cycles, color, duration):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=1,
                blend=True,
                color=Colors.black.value
            ),
            AnimationStep(
                duration_ms=duration,
                blend=True,
                color=color.value
            ),
            AnimationStep(
                duration_ms=300,
                blend=True,
                color=color.value
            ),
            AnimationStep(
                duration_ms=300,
                blend=True,
                color=Colors.black.value
            )
        ]
    )


def blink_animation(cycles, color):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=500,
                blend=False,
                color=color.value
            ),
            AnimationStep(
                duration_ms=500,
                blend=False,
                color=Colors.black.value
            )
        ]
    )


def flip_animation(cycles, color_one, color_two, duration_one, duration_two):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=duration_one,
                blend=False,
                color=color_one.value
            ),
            AnimationStep(
                duration_ms=duration_two,
                blend=False,
                color=color_two.value
            )
        ]
    )


def pulse_animation(cycles, color_one, color_two):
    return LightAnimation(
        repeat=cycles,
        target_lights=["1"],
        sequence=[
            AnimationStep(
                duration_ms=500,
                blend=True,
                color=color_one.value
            ),
            AnimationStep(
                duration_ms=1000,
                blend=True,
                color=color_two.value
            )
        ]
    )
