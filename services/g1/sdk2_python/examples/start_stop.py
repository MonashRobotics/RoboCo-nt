import time
import typer
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
import os
import sys

app = typer.Typer()

connection_interface = os.environ.get("CONNECTION_IF")
if not connection_interface:
    print("Error: Environment variable 'CONNECTION_IF' is not set.")
    print("Please run: export CONNECTION_IF='your_interface_name'")
    sys.exit(1)

@app.command()
def start():
    """Starts the robot: Damping -> Lock Standing -> Running."""
    ChannelFactoryInitialize(0, connection_interface)
    robot = LocoClient()
    robot.SetTimeout(10.0)
    robot.Init()
    print("Entering DAMPING ...")
    robot.SetFsmId(1)  # Damping
    time.sleep(3)
    print("Entering LOCK STANDING ...")
    robot.SetFsmId(4)
    input("press ENTER to start RUNNING MODE ...")
    print("Entering RUNNING ...")
    robot.SetFsmId(801)  # Running

@app.command()
def stop():
    """Stops the robot: Locked Standing -> Damping -> Zero Moment."""
    ChannelFactoryInitialize(0, connection_interface)
    robot = LocoClient()
    robot.SetTimeout(10.0)
    robot.Init()
    print("Entering LOCKED STANDING ...")
    robot.SetFsmId(4)  # Locked Standing
    time.sleep(1)
    print("Entering DAMPING ..")
    robot.SetFsmId(1)
    time.sleep(1)
    print("Entering ZERO MOMENT ...")
    robot.SetFsmId(0)  # Zero Moment

if __name__ == "__main__":
    app()

