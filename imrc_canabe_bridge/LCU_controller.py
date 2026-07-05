#!/usr/bin/env python3
from imrc_messages.msg import EcanCommand
from rclpy.publisher import Publisher
import rclpy
from rclpy.node import Node

class LCU_controller:
    def __init__(self, node: Node): 
        self.node = node 

    def LCU_control(self, publisher: Publisher,MODE: str, LED_ID: int, Color: str, duration: int = 1000):
        # Parse the color string into RGB values
        if Color == "red":
            R, G, B = 255, 0, 0
        elif Color == "green":
            R, G, B = 0, 255, 0
        elif Color == "blue":
            R, G, B = 0, 0, 255
        else:
            self.node.get_logger().error(f"Invalid color: {Color}. Please use 'red', 'green', or 'blue'.")
        
        if MODE == "set_rgb":
            LCU_controller._set_rgb(publisher, LED_ID, R, G, B)
        elif MODE == "turn_off":
            LCU_controller._turn_off(publisher, LED_ID)
        elif MODE == "set_blink":
            LCU_controller._set_blink(publisher, LED_ID, R, G, B, duration)
        elif MODE == "set_bloom":
            LCU_controller._set_bloom(publisher, LED_ID, R, G, B, duration)
        else:
            self.node.get_logger().error(f"Invalid MODE: {MODE}. Please use 'set_rgb', 'turn_off', 'set_blink', or 'set_bloom'.")
        

    
    def _set_rgb(publisher: Publisher,LED_ID: int, R: int, G: int, B: int):
        msg = EcanCommand()
        msg.unit_code = 20
        msg.unit_index = 1
        msg.payload_index = 3
        msg.payload_entry = 0
        msg.data = [LED_ID, 0, R, G, B]
        
        publisher.publish(msg)

    
    def _turn_off(publisher: Publisher, LED_ID: int):
        msg = EcanCommand()
        msg.unit_code = 20
        msg.unit_index = 1
        msg.payload_index = 3
        msg.payload_entry = 0
        msg.data = [LED_ID, 0, 0, 0, 0]
        
        publisher.publish(msg)

    
    def _set_blink(publisher: Publisher , LED_ID: int, R: int, G: int, B: int, time: int):
        msg = EcanCommand()
        msg.unit_code = 20
        msg.unit_index = 1
        msg.payload_index = 3
        msg.payload_entry = 0
        msg.data = [LED_ID, 1, R, G, B, time]
        
        publisher.publish(msg)

    
    def _set_bloom(publisher: Publisher , LED_ID: int, R: int, G: int, B: int, time: int):
        msg = EcanCommand()
        msg.unit_code = 20
        msg.unit_index = 1
        msg.payload_index = 3
        msg.payload_entry = 0
        msg.data = [LED_ID, 2, R, G, B, time]
        
        publisher.publish(msg)
