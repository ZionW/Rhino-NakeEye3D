"""Send synthetic head motion and half-grip input; no webcam required."""
import json
import math
import socket
import time

def sample(t):
    grip = 5 <= t % 12 < 9
    return dict(X=.1 * math.sin(t), Y=.05 * math.cos(t), Z=.04 * math.sin(t / 2),
                Grip=grip, HandX=.2 * math.sin(t), HandY=.1 * math.cos(t))

if __name__ == '__main__':
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
        started = time.monotonic()
        try:
            while True:
                connection.sendto(json.dumps(sample(time.monotonic() - started)).encode(), ('127.0.0.1', 39539))
                time.sleep(1 / 30)
        except KeyboardInterrupt:
            pass
