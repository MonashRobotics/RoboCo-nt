# To run the full manipulation stack
source install/setup.bash && colcon build --symlink-install && source install/setup.bash && ros2 launch g1pilot bringup_launcher.launch.py

# To test openSOT
source install/setup.bash && colcon build --symlink-install && source install/setup.bash && ros2 run g1pilot opensot_solver --ros-args -p use_robot:=true -p interface:="eno1"


# Test manipulation only (not working for some reason.)

source install/setup.bash && colcon build && source install/setup.bash && ros2 launch g1pilot bringup_launcher.launch.py use_robot:=false publish_joint_states_opensot:=true