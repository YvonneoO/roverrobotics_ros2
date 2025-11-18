#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    rover_pkg_share = FindPackageShare('rover')
    config_dir = PathJoinSubstitution([rover_pkg_share, 'config'])
    controller_launch = PythonLaunchDescriptionSource(
        [rover_pkg_share, '/launch/f710_controller.launch.py'])
    controller_node = IncludeLaunchDescription(controller_launch)

    localization_config = PathJoinSubstitution([config_dir, 'localization_ekf.yaml'])
    rover_driver_config = PathJoinSubstitution([config_dir, 'pro_config.yaml'])

    driver_config_arg = DeclareLaunchArgument(
        'hardware_config', default_value=rover_driver_config,
        description='Full path to the roverrobotics_driver hardware config YAML'
    )
    localization_config_arg = DeclareLaunchArgument(
        'localization_config', default_value=localization_config,
        description='Full path to ekf_filter_node parameters'
    )
    camera_input_arg = DeclareLaunchArgument(
        'camera_input', default_value='0',
        description='Video device index consumed by image_pub.py'
    )

    rover_driver_node = Node(
        package='roverrobotics_driver',
        executable='roverrobotics_driver',
        name='roverrobotics_driver',
        parameters=[
            LaunchConfiguration('hardware_config'),
            {'speed_topic': LaunchConfiguration('cmd_vel_topic')},
        ],
        respawn=True,
        respawn_delay=1.0,
        output='screen'
    )

    localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[LaunchConfiguration('localization_config')]
    )

    image_pub_node = Node(
        package='rover',
        executable='image_pub.py',
        name='image_publisher',
        arguments=['-i', LaunchConfiguration('camera_input')],
        output='screen'
    )

    return LaunchDescription([
        driver_config_arg,
        localization_config_arg,
        camera_input_arg,
        controller_node,
        rover_driver_node,
        localization_node,
        image_pub_node,
    ])
