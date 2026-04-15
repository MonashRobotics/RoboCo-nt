import time
import sys
import os

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import (
    MotionSwitcherClient,
)

import numpy as np

kPi = 3.141592654
kPi_2 = 1.57079632
kPi_4 = kPi_2 / 2


class G1JointIndex:
    # Left leg
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleB = 4
    LeftAnkleRoll = 5
    LeftAnkleA = 5

    # Right leg
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleB = 10
    RightAnkleRoll = 11
    RightAnkleA = 11

    WaistYaw = 12
    WaistRoll = 13  # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistA = 13  # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistPitch = 14  # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistB = 14  # NOTE: INVALID for g1 23dof/29dof with waist locked

    # Left arm
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20  # NOTE: INVALID for g1 23dof
    LeftWristYaw = 21  # NOTE: INVALID for g1 23dof

    # Right arm
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27  # NOTE: INVALID for g1 23dof
    RightWristYaw = 28  # NOTE: INVALID for g1 23dof

    kNotUsedJoint = 29  # NOTE: Weight


class Custom:
    def __init__(self):
        self.time_ = 0.0
        self.control_dt_ = 0.02
        self.duration_ = 3.0
        self.counter_ = 0
        self.weight = 0.0
        self.weight_rate = 0.2
        self.kp = 60.0
        self.kd = 1.5
        self.dq = 0.0
        self.tau_ff = 0.0
        self.mode_machine_ = 0
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.low_state = None
        self.first_update_low_state = False
        self.crc = CRC()
        self.done = False

        """
        Joint list: (Motors rotate counterclockwise)
        [
        Left shoulder 1,
        Left shoulder 2,
        Left shoulder 3,
        Left Elbow 1,
        Left Elbow 2,
        Left Wrist 1,
        Left Wrist 2,
        Right shoulder 1,
        Right shoulder 2,
        Right shoulder 3,
        Right Elbow 1,
        Right Elbow 2,
        Right Wrist 1,
        Right Wrist 2,
        Waist (Upper body rotate),
        0,
        0,
        ]
        """

        self.demo_sequence = [
            [
                0.0,
                kPi_2,
                0.0,
                kPi_2,
                0.0,
                0.0,
                0.0,
                0.0,
                -kPi_2,
                0.0,
                kPi_2,
                0.0,
                0.0,
                0.0,
                0,
                0,
                0,
            ],
            [
                0.0,
                kPi_2 / 2,
                0.0,
                kPi_2,
                0.0,
                0.0,
                0.0,
                0.0,
                -kPi_2 / 2,
                0.0,
                kPi_2,
                0.0,
                0.0,
                0.0,
                0,
                0,
                0,
            ],
            [
                0.0,
                kPi_2 / 2,
                0.0,
                0.0,
                0.0,
                kPi_2,
                -kPi_2,
                0.0,
                -kPi_2 / 2,
                0.0,
                0.0,
                0.0,
                kPi_2,
                kPi_2,
                0,
                0,
                0,
            ],
            [
                0.0,
                kPi_2 / 2,
                0.0,
                0.0,
                -kPi_2,
                kPi_2,
                -kPi_2,
                0.0,
                -kPi_2 / 2,
                0.0,
                0.0,
                kPi_2,
                kPi_2,
                kPi_2,
                0,
                0,
                0,
            ],
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0,
                0,
                0,
            ],
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                kPi_2,
                0,
                0,
            ],
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0,
                0,
                0,
            ],
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                -kPi_2,
                0,
                0,
            ],
        ]

        self.arm_joints = [
            G1JointIndex.LeftShoulderPitch,
            G1JointIndex.LeftShoulderRoll,
            G1JointIndex.LeftShoulderYaw,
            G1JointIndex.LeftElbow,
            G1JointIndex.LeftWristRoll,
            G1JointIndex.LeftWristPitch,
            G1JointIndex.LeftWristYaw,
            G1JointIndex.RightShoulderPitch,
            G1JointIndex.RightShoulderRoll,
            G1JointIndex.RightShoulderYaw,
            G1JointIndex.RightElbow,
            G1JointIndex.RightWristRoll,
            G1JointIndex.RightWristPitch,
            G1JointIndex.RightWristYaw,
            G1JointIndex.WaistYaw,
            G1JointIndex.WaistRoll,
            G1JointIndex.WaistPitch,
        ]

    def Init(self):
        # create publisher #
        self.arm_sdk_publisher = ChannelPublisher("rt/arm_sdk", LowCmd_)
        self.arm_sdk_publisher.Init()

        # create subscriber #
        self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_subscriber.Init(self.LowStateHandler, 10)

    def Start(self):
        while self.first_update_low_state == False:
            time.sleep(1)

        if self.first_update_low_state == True:
            print("Moving to zero pose...")
            self.move_to_target(0, 3)
            for i in range(len(self.demo_sequence)):
                if i - 1 >= 0:
                    self.move_to_target(self.demo_sequence[i], 3, last_pose=self.demo_sequence[i-1])
                else:
                    self.move_to_target(self.demo_sequence[i], 3)
            self.move_to_target(0, 3)
            self.release_arm_sdk()

    def LowStateHandler(self, msg: LowState_):
        self.low_state = msg

        if self.first_update_low_state == False:
            self.first_update_low_state = True

    def move_to_target(self, target_pose, duration, last_pose=None):
        timer = 0.0
        while timer <= duration:
            ratio = np.clip(timer / duration, 0.0, 1.0)

            self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = (
                1  # 1:Enable arm_sdk, 0:Disable arm_sdk
            )

            for i, joint in enumerate(self.arm_joints):

                if target_pose == 0:
                    q = (1.0 - ratio) * self.low_state.motor_state[joint].q
                else:
                    if last_pose and target_pose[i] == last_pose[i]:
                        q = target_pose[i]
                    else:
                        q = (
                            ratio * target_pose[i]
                            + (1.0 - ratio) * self.low_state.motor_state[joint].q
                        )

                self.low_cmd.motor_cmd[joint].tau = 0.0
                self.low_cmd.motor_cmd[joint].q = q
                self.low_cmd.motor_cmd[joint].dq = 0.0
                self.low_cmd.motor_cmd[joint].kp = self.kp
                self.low_cmd.motor_cmd[joint].kd = self.kd

            self.low_cmd.crc = self.crc.Crc(self.low_cmd)
            self.arm_sdk_publisher.Write(self.low_cmd)
            timer += self.control_dt_
            time.sleep(self.control_dt_)

    def release_arm_sdk(self):
        print("Releasing arm SDK...")
        timer = 0.0
        while timer <= 1.0:
            for i, joint in enumerate(self.arm_joints):
                ratio = np.clip(timer / 1.0, 0.0, 1.0)
                self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = (
                    1 - ratio
                )  # 1:Enable arm_sdk, 0:Disable arm_sdk

            self.low_cmd.crc = self.crc.Crc(self.low_cmd)
            self.arm_sdk_publisher.Write(self.low_cmd)
            timer += self.control_dt_
            time.sleep(self.control_dt_)
        self.done = True


def main(args=None):
    print(
        "WARNING: Please ensure there are no obstacles around the robot while running this example."
    )
    input("Press Enter to continue...")

    connection_interface = os.environ.get("CONNECTION_IF")
    if not connection_interface:
        print("Error: Environment variable 'CONNECTION_IF' is not set.")
        print("Please run: export CONNECTION_IF='your_interface_name'")
        sys.exit(1)
    ChannelFactoryInitialize(0, connection_interface)

    custom = Custom()
    custom.Init()
    custom.Start()

    while True:
        time.sleep(1)
        if custom.done:
            print("Done!")
            sys.exit(-1)


if __name__ == "__main__":
    main()
