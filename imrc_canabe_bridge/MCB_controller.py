#!/usr/bin/env python3
from imrc_messages.msg import EcanCommand
from rclpy.publisher import Publisher
import rclpy

class cmd_vel_controller:
    def __init__(self):
        pass

    @classmethod
    def cmd_vel_send(cls, publisher: Publisher,unit_index: int,x: float, y: float,yaw: float):
        x = int(x * 1000)
        y = int(y * 1000)
        yaw = int(yaw * 1000)

        x = max(-32768, min(32767, x))
        y = max(-32768, min(32767, y))
        yaw = max(-32768, min(32767, yaw))

        x_high_byte = (x >> 8) & 0xFF
        x_low_byte = x & 0xFF
        y_high_byte = (y >> 8) & 0xFF
        y_low_byte = y & 0xFF 
        yaw_high_byte = (yaw >> 8) & 0xFF
        yaw_low_byte = yaw & 0xFF

        msg = EcanCommand()
        msg.unit_code = 16
        msg.unit_index = unit_index
        msg.payload_index = 3
        msg.payload_entry = 0
        msg.data = [x_high_byte, x_low_byte, y_high_byte, y_low_byte, yaw_high_byte, yaw_low_byte]
        
        publisher.publish(msg)   

