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

from . import animations, directives
Colors = animations.Colors

# The skill states are the different parts of the skill.
SKILL_STATES = {
    # Roll Call mode performs roll call and button registration.
    # https://developer.amazon.com/docs/echo-button-skills/discover-echo-buttons.html
    "ROLL_CALL_MODE": "",
    "PLAY_MODE": "_PLAY_MODE",
    # Exit mode performs the actions described in
    # https://developer.amazon.com/docs/echo-button-skills/exit-echo-button-skill.html
    "EXIT_MODE": "_EXIT_MODE"
}

# We'll use an audio sample of a ticking clock to play whenever the skill is waiting for button presses
#  This is an audio file from the ASK Soundbank: https://developer.amazon.com/docs/custom-skills/foley-sounds.html
WAITING_AUDIO = "<audio src=\"https://s3.amazonaws.com/ask-soundlibrary/foley/amzn_sfx_rhythmic_ticking_30s_01.mp3\"/>"

# The following are going to be the colors we allow in the skill
COLORS_ALLOWED = [Colors.blue.name, Colors.green.name, Colors.red.name]
BREATH_COLORS = {Colors.blue: Colors.light_blue,
                 Colors.green: Colors.light_green, Colors.red: Colors.light_red}

# Define animations to be played on button down and button up that are like the default animations on the buttons
# We'll use these animations when resetting play state
# See: https://developer.amazon.com/docs/echo-button-skills/control-echo-buttons.html#animate
DEFAULT_ANIMATION_BUTTON_DOWN = animations.fade_out_animation(
    1, Colors.blue, 200)
DEFAULT_ANIMATION_BUTTON_UP = animations.solid_animation(1, Colors.black, 100)
