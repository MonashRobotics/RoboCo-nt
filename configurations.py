from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Literal

ROSDistro = Literal["noetic", "jazzy"]


@dataclass
class HardwareOption:
    key: str
    name: str
    compatible_ros_distros: list[ROSDistro]

@dataclass
class Robot:
    key: str
    name: str
    compatible_hardware: list[HardwareOption]
    available_service: list[RobotService]

@dataclass
class RobotService:
    key: str
    name: str
    long_description: str
    compatible_ros_distros: list[ROSDistro]

moveit_panda = RobotService("moveit", "Ros Moveit", "Moveit to control joint space, if you are familiar with Moveit, this is the way to go", ["noetic"])
armer_panda = RobotService("armer", "armer package from qut",  "essentially a Python interface that let you control robot joint position, velocity as well as EE position and velocity easily", ["noetic"])
sdk_g1 = RobotService("sdk2_python", "Unitree SDK to control", "", [])
g1pilot_g1 = RobotService("g1pilot", "Control stack g1pilot", "", ["jazzy"])

realsense_camera = HardwareOption("realsense", "RealSense Camera", ["noetic", "jazzy"])
kinect_camera = HardwareOption("kinect2", "Kinect Camera", ["noetic"])


panda = Robot("panda", "Panda", [realsense_camera], [moveit_panda, armer_panda])
g1 = Robot("g1", "Unitree G1", [realsense_camera], [sdk_g1, g1pilot_g1])

robots = {
    "panda": panda,
    "g1": g1
}

hardwares = {
    "realsense": realsense_camera,
    "kinect2": kinect_camera
}