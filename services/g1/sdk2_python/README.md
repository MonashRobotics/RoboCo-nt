# Scripts
Move the robot upper body
```
/opt/robot/bin/python3 /app/examples/start_stop.py start
/opt/robot/bin/python3 /app/examples/upper_body_demo.py
```

Move the hand
```
/opt/hand/bin/python3 /app/examples/hand_publish.py
```

Visualize the hand data (please remember to do `xhost +local:docker` on your host)
```
/opt/hand/bin/python3 /app/examples/hand_subscribe.py
```

Stop the robot
```
/opt/robot/bin/python3 /app/examples/start_stop.py stop
```


# FAQ
Q: If you see `Exception: channel factory init error.`
A: Often times, it means your `CONNECTION_IF` in `.env` is not correct, please check.