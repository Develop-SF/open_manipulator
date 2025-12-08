# Copyright 2023 Intel Corporation. All Rights Reserved.
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

# DESCRIPTION #
# ----------- #
# Use this launch file to launch 2 devices.
# The Parameters available for definition in the command line for each camera are described in
# rs_launch.configurable_parameters
# For each device, the parameter name was changed to include an index.
# For example: to set camera_name for device1 set parameter camera_name1.
# command line example:
# ros2 launch realsense2_camera rs_multi_camera_launch.py \
#     camera_name1:=D400 \
#     device_type1:=d4 \
#     device_type2:=l5

"""Launch realsense2_camera node."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import SetRemap


def generate_launch_description():
    # 換成 rs_multi_camera_launch.py
    rs_multi_launch = os.path.join(
        get_package_share_directory('realsense2_camera'),
        'launch',
        'rs_multi_camera_launch.py'
    )

    rs_multi_include = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rs_multi_launch),
        launch_arguments={
            # cam 1 (wrist realsense D405)
            'serial_no1': "'218622276423'",
            'camera_name1': 'cam_wrist',
            'camera_namespace1': 'camera',
            'depth_module.depth_profile1': '480x270x15',
            'depth_module.color_profile1': '424x240x15',
            'pointcloud.enable1': 'false',
            'colorizer.enable1': 'true',

            # cam 2 (top realsense D435)
            'serial_no2': "'233522078616'",
            'camera_namespace2': 'camera',
            'camera_name2': 'cam_top',
            'depth_module.depth_profile2': '480x270x15',
            'rgb_camera.color_profile2': '424x240x15',
            'pointcloud.enable2': 'false',
            'colorizer.enable2': 'true',

        }.items(),
    )

    rs_group = GroupAction(
        actions=[
            rs_multi_include,
        ]
    )

    return LaunchDescription([
        rs_group
    ])