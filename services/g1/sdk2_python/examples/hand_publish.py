import time
import os

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.utils.thread import Thread

from inspire_sdkpy import inspire_hand_defaut, inspire_dds
import numpy as np

if __name__ == '__main__':

    # Read the connection interface from the environment variable
    connection_if = os.environ.get('CONNECTION_IF')
    if connection_if:
        ChannelFactoryInitialize(0, connection_if)
    else:
        ChannelFactoryInitialize(0)
        
    # Create a publisher to publish the data defined in UserData class
    pubr = ChannelPublisher("rt/inspire_hand/ctrl/r", inspire_dds.inspire_hand_ctrl)
    pubr.Init()
    
    publ = ChannelPublisher("rt/inspire_hand/ctrl/l", inspire_dds.inspire_hand_ctrl)
    publ.Init()
    cmd = inspire_hand_defaut.get_inspire_hand_ctrl()
    short_value=1000

    cmd.angle_set=[0,0,0,0,1000,1000]
    cmd.mode=0b0001
    publ.Write(cmd)
    pubr.Write(cmd)

    time.sleep(1.0)

    cmd.angle_set=[0,0,0,0,0,1000] 
    cmd.mode=0b0001
    publ.Write(cmd)
    pubr.Write(cmd)

    time.sleep(3.0)

    for cnd in range(100000): 

        # Register start address, 0x05CE corresponds to 1486
        start_address = 1486            
        num_registers = 6  # 6 registers
        # Generate the list of values to write, each register takes a short value

        if (cnd+1) % 10 == 0:
            short_value = 1000-short_value  # The short value to write

        values_to_write = [short_value] * num_registers
        values_to_write[-1]=1000-values_to_write[-1]
        values_to_write[-2]=1000-values_to_write[-2]

        value_to_write_np=np.array(values_to_write)
        value_to_write_np=np.clip(value_to_write_np,200,800)
        # value_to_write_np=800

        # Implement combination modes in binary format
        # mode 0: 0000 (No operation)
        # mode 1: 0001 (Angle)
        # mode 2: 0010 (Position)
        # mode 3: 0011 (Angle + Position)
        # mode 4: 0100 (Force control)
        # mode 5: 0101 (Angle + Force control)
        # mode 6: 0110 (Position + Force control)
        # mode 7: 0111 (Angle + Position + Force control)
        # mode 8: 1000 (Velocity)
        # mode 9: 1001 (Angle + Velocity)
        # mode 10: 1010 (Position + Velocity)
        # mode 11: 1011 (Angle + Position + Velocity)
        # mode 12: 1100 (Force control + Velocity)
        # mode 13: 1101 (Angle + Force control + Velocity)
        # mode 14: 1110 (Position + Force control + Velocity)
        # mode 15: 1111 (Angle + Position + Force control + Velocity)  
        cmd.angle_set=value_to_write_np.tolist()
        cmd.mode=0b0001
        
        # Publish message
        if publ.Write(cmd) and pubr.Write(cmd):
            # print("Publish success. msg:", cmd.crc)
            pass
        else:
            print("Waiting for subscriber.")

        time.sleep(0.1)