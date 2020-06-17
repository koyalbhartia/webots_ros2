#!/usr/bin/env python

# Copyright 1996-2020 Cyberbotics Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Launch Webots and ROS2 driver."""

import sys
import os
import launch
from launch import LaunchDescription
from launch.actions import RegisterEventHandler, EmitEvent
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from webots_ros2_core.utils import ControllerLauncher


def generate_launch_description():
    synchronization = LaunchConfiguration('synchronization', default=False)
    params = {arg.split(':=')[0]: arg.split(':=')[1] for arg in sys.argv if ':=' in arg}

    if 'world' not in params:
        print('No world parameter has been found, please define it!')
        sys.exit(1)

    if not os.path.exists(params['world']):
        print('World doesn\'t exist')
        sys.exit(2)

    params['mode'] = params.setdefault('mode', 'realtime')

    # Webots
    arguments = [
        '--mode=' + params['mode'],
        '--world=' + params['world']
    ]
    webots = Node(
        package='webots_ros2_core',
        node_executable='webots_launcher',
        arguments=arguments,
        output='screen'
    )

    # Driver node
    controller = ControllerLauncher(
        package='webots_ros2_core',
        node_executable='webots_node',
        parameters=[{
            'synchronization': synchronization,
            'use_joint_state_publisher': True
        }],
        output='screen'
    )

    # Robot state publisher
    initial_robot_description = '<?xml version="1.0"?><robot name="dummy"><link name="base_link"></link></robot>'
    robot_state_publisher = Node(
        package='robot_state_publisher',
        node_executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': initial_robot_description}]
    )

    return LaunchDescription([
        robot_state_publisher,
        webots,
        controller,

        # Shutdown launch when Webots exits.
        RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=webots,
                on_exit=[EmitEvent(event=launch.events.Shutdown())],
            )
        )
    ])