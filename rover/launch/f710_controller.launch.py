#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    rover_pkg_share = FindPackageShare('rover')
    config_dir = PathJoinSubstitution([rover_pkg_share, 'config'])

    controller_config = PathJoinSubstitution([config_dir, 'logitech_f710_mapper.yaml'])
    topics_config = PathJoinSubstitution([config_dir, 'topics.yaml'])

    joy_dev_arg = DeclareLaunchArgument(
        'joy_dev', default_value='/dev/input/js0',
        description='Linux joystick device for the Logitech F710'
    )
    deadzone_arg = DeclareLaunchArgument(
        'deadzone', default_value='0.10',
        description='Joystick deadzone passed to joy_node'
    )
    autorepeat_arg = DeclareLaunchArgument(
        'autorepeat_rate', default_value='30.0',
        description='Autorepeat rate for joy_node buttons (Hz)'
    )
    cmd_vel_topic_arg = DeclareLaunchArgument(
        'cmd_vel_topic', default_value='/cmd_vel',
        description='Twist topic that will consume joystick commands'
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='f710_joy_driver',
        parameters=[{
            'dev': LaunchConfiguration('joy_dev'),
            'deadzone': LaunchConfiguration('deadzone'),
            'autorepeat_rate': LaunchConfiguration('autorepeat_rate'),
            'default_trig_val': 0.0,
        }],
        output='screen'
    )

    mapper_node = Node(
        package='roverrobotics_input_manager',
        executable='joys_manager.py',
        name='f710_mapper',
        parameters=[{
            'controller': controller_config,
            'topics': topics_config,
        }],
        remappings=[('/cmd_vel/joystick', LaunchConfiguration('cmd_vel_topic'))],
        output='screen'
    )

    return LaunchDescription([
        joy_dev_arg,
        deadzone_arg,
        autorepeat_arg,
        cmd_vel_topic_arg,
        joy_node,
        mapper_node,
    ])
