#!/usr/bin/env python3
from imrc_messages.msg import EcanCommand
from rclpy.publisher import Publisher

class heartbeat:
    @staticmethod
    def send_heartbeat(publisher: Publisher):
        msg = EcanCommand()
        msg.unit_code = 2
        msg.unit_index = 1

        msg.payload_index = 1
        msg.payload_entry = 1
        
        msg.data = [1]
        
        publisher.publish(msg)