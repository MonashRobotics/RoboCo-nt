from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from inspire_sdkpy import inspire_hand_defaut, inspire_dds

import numpy as np
import colorcet  
import time
import threading
import os
import sys

from inspire_sdkpy import qt_tabs, inspire_sdk, inspire_hand_defaut

class DDSHandler():
   
    def __init__(self, network=None, sub_touch=True, LR='r'):
        super().__init__()
        if network is None:
            ChannelFactoryInitialize(0)
        else:
            ChannelFactoryInitialize(0, network)
        self.data = inspire_hand_defaut.data_sheet
        if sub_touch:
            self.sub_touch = ChannelSubscriber("rt/inspire_hand/touch/" + LR, inspire_dds.inspire_hand_touch)
            self.sub_touch.Init(self.update_data_touch, 10)
        
        self.sub_states = ChannelSubscriber("rt/inspire_hand/state/" + LR, inspire_dds.inspire_hand_state)
        self.sub_states.Init(self.update_data_state, 10)
        self.touch = {}
        self.states = {}
        self.data_touch_lock = threading.Lock()
        self.data_state_lock = threading.Lock()

    # Function to update the data/graphics
    def update_data_touch(self, msg: inspire_dds.inspire_hand_touch):
        with self.data_touch_lock:
            start_time = time.time()
            for i, (name, addr, length, size, var) in enumerate(self.data):
                value = getattr(msg, var)
                if value is not None:
                    matrix = np.array(value).reshape(size)
                    self.touch[var] = matrix
            end_time = time.time() 
            elapsed_time = end_time - start_time
            
    def update_data_state(self, states_msg: inspire_dds.inspire_hand_state):
        with self.data_state_lock:
            self.states = {
                'POS_ACT': states_msg.pos_act,
                'ANGLE_ACT': states_msg.angle_act,
                'FORCE_ACT': states_msg.force_act,
                'CURRENT': states_msg.current,
                'ERROR': states_msg.err,
                'STATUS': states_msg.status,
                'TEMP': states_msg.temperature
            }
            
    def read(self):
        with self.data_state_lock, self.data_touch_lock:
            return {'states': self.states, 'touch': self.touch}


if __name__ == "__main__":

    connection_if = os.environ.get('CONNECTION_IF')
    ddsHandler = DDSHandler(network=connection_if, LR='r')
    # ddsHandler = DDSHandler(LR='l')

    app = qt_tabs.QApplication(sys.argv)
    window = qt_tabs.MainWindow(data_handler=ddsHandler, dt=50, name="DDS Subscribe") # Update every 55 ms
    window.reflash()
    window.show()
    sys.exit(app.exec_())