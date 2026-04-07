from __future__ import annotations

from dataclasses import dataclass

from typing_extensions import Literal

ROSDistro = Literal["noetic", "foxy", "humble"]


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
    compatible_ros_distros: list[ROSDistro]

moveit_panda = RobotService("moveit", "Moveit to control joint space, if you are familiar with Moveit, this is the way to go", ["noetic"])
moveit_ur5 = RobotService("moveit", "Moveit to control joint space, if you are familiar with Moveit, this is the way to go", ["noetic"])
armer_panda = RobotService("armer", "armer package from qut, essentially a Python interface that let you control robot joint position, velocity as well as EE position and velocity easily", ["noetic"])

realsense_camera = HardwareOption("realsense", "RealSense Camera", ["melodic", "noetic", "foxy", "humble"])
robotiq_2f85_gripper = HardwareOption("robotiq_2f85_gripper", "Robotiq 2F-85 Gripper", ["melodic", "noetic"])
robotiq_ft300_forcetorque = HardwareOption(
    "robotiq_ft300_forcetorque", "Robotiq FT-300 Force-Torque Sensor", ["melodic", "noetic"]
)
papillarray = HardwareOption("papillarray", "Contactile Papillarray Tactile Sensor", ["melodic", "noetic"])


panda = Robot("panda", "Panda", [realsense_camera], [moveit_panda, armer_panda])
ur5 = Robot(
    "ur5",
    "UR5",
    [realsense_camera, robotiq_2f85_gripper, robotiq_ft300_forcetorque, papillarray],
    [moveit_ur5]
)

robots = {
    "panda": panda,
    "ur5": ur5
}