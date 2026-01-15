#!/usr/bin/env python3
#
# Copyright 2024 ROBOTIS CO., LTD.
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
#
# Author: Wonho Yun, Sungho Woo, Woojin Wie

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.actions import RegisterEventHandler
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    # Declare launch arguments
    declared_arguments = [
        DeclareLaunchArgument(
            'namespace',
            default_value="",
            description="Namespace for the robot (choose '', 'la_robotis', or 'ra_robotis')",
        ),
        DeclareLaunchArgument(
            'start_rviz', default_value='false', description='Whether to execute rviz2'
        ),
        DeclareLaunchArgument(
            'prefix',
            default_value="",
            description="Prefix of the joint and link names (choose '', 'la_robotis_', or 'ra_robotis_')",
        ),
        DeclareLaunchArgument(
            'use_sim',
            default_value='false',
            description='Start robot in Gazebo simulation.',
        ),
        DeclareLaunchArgument(
            'use_mock_hardware',
            default_value='false',
            description='Use fake hardware mirroring command.',
        ),
        DeclareLaunchArgument(
            'mock_sensor_commands',
            default_value='false',
            description='Enable fake sensor commands.',
        ),
        DeclareLaunchArgument(
            'init_position',
            default_value='false',
            description='Whether to launch the init_position node',
        ),
        DeclareLaunchArgument(
            'ros2_control_type',
            default_value='omy_f3m_position',
            description='Type of ros2_control',
        ),
        DeclareLaunchArgument(
            'init_position_file',
            default_value='initial_positions.yaml',
            description='Path to the initial position file',
        ),
        DeclareLaunchArgument(
            'publish_tf',
            default_value='true',
            description='Whether to run robot_state_publisher on this machine',
        ),
    ]

    # Launch configurations
    namespace = LaunchConfiguration('namespace')
    start_rviz = LaunchConfiguration('start_rviz')
    prefix = LaunchConfiguration('prefix')
    use_sim = LaunchConfiguration('use_sim')
    use_mock_hardware = LaunchConfiguration('use_mock_hardware')
    mock_sensor_commands = LaunchConfiguration('mock_sensor_commands')
    init_position = LaunchConfiguration('init_position')
    ros2_control_type = LaunchConfiguration('ros2_control_type')
    init_position_file = LaunchConfiguration('init_position_file')
    publish_tf = LaunchConfiguration('publish_tf')

    # Generate URDF file using xacro
    urdf_file = Command([
        PathJoinSubstitution([FindExecutable(name='xacro')]),
        ' ',
        PathJoinSubstitution([
            FindPackageShare('open_manipulator_description'),
            'urdf',
            'omy_f3m',
            'omy_f3m.urdf.xacro',
        ]),
        ' ',
        'prefix:=',
        prefix,
        ' ',
        'use_sim:=',
        use_sim,
        ' ',
        'use_mock_hardware:=',
        use_mock_hardware,
        ' ',
        'mock_sensor_commands:=',
        mock_sensor_commands,
        ' ',
        'ros2_control_type:=',
        ros2_control_type,
    ])

    # Paths for configuration files
    controller_manager_config = PathJoinSubstitution([
        FindPackageShare('open_manipulator_bringup'),
        'config',
        'omy_f3m_follower_ai',
        'hardware_controller_manager.yaml',
    ])

    rviz_config_file = PathJoinSubstitution([
        FindPackageShare('open_manipulator_description'),
        'rviz',
        'open_manipulator.rviz',
    ])

    trajectory_params_file = PathJoinSubstitution([
        FindPackageShare('open_manipulator_bringup'),
        'config',
        'omy_f3m_follower_ai',
        init_position_file,
    ])

    # Define nodes
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[{'robot_description': urdf_file}, controller_manager_config],
        output='both',
        condition=UnlessCondition(use_sim),
        remappings=[
            ('joint_states', '/joint_states'),
            ('/arm_controller/joint_trajectory', '/robotis_leader/joint_trajectory')],
    )

    robot_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            [prefix, 'arm_controller'],
            [prefix, 'joint_state_broadcaster'],
            # [prefix, 'gpio_command_controller'],
        ],
        output='both',
        parameters=[{'robot_description': urdf_file}],
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': urdf_file, 'use_sim_time': use_sim}],
        output='both',
        condition=IfCondition(publish_tf),
    )

    joint_trajectory_executor = Node(
        package='open_manipulator_bringup',
        executable='joint_trajectory_executor',
        parameters=[trajectory_params_file],
        output='both',
        condition=IfCondition(init_position),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_file],
        output='both',
        condition=IfCondition(start_rviz),
    )

    # Event handlers to ensure order of execution
    delay_rviz_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=robot_controller_spawner, on_exit=[rviz_node]
        )
    )

    delay_joint_trajectory_executor_after_controllers = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=robot_controller_spawner,
            on_exit=[joint_trajectory_executor],
        )
    )

    group = GroupAction([
        PushRosNamespace(namespace),
        control_node,
        robot_controller_spawner,
        robot_state_publisher_node,
        delay_rviz_after_joint_state_broadcaster_spawner,
        delay_joint_trajectory_executor_after_controllers,
    ])

    return LaunchDescription(
        declared_arguments
        + [group]
    )