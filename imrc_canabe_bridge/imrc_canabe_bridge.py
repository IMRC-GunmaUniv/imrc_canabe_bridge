import serial
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import Bool
from geometry_msgs.msg import Twist
import math
import threading

from imrc_messages.msg import LCU
from imrc_messages.msg import EcanCommand

from imrc_canabe_bridge.LCU_controller import *
from imrc_canabe_bridge.heartbeat import *
from imrc_canabe_bridge.MCB_controller import *



class imrc_canabe_bridge(Node):
    def __init__(self):
        super().__init__('imrc_canabe_bridge')

        self.loopWaitTime = 0.001

        self.logger = self.get_logger()

        self.canabe_pub = self.create_publisher(EcanCommand, '/can_tx_demo', 10)
        
        self.heartbeat_timer = self.create_timer(0.5, self.heartbeat_timer_callback)
        self.topic_subscribe()

        self.logger.info("cannabe bridge initialized.")    

    def topic_subscribe(self):
        #サブスクライバー
        self.create_subscription(LCU, 'lcu', self.lcu_callback, 10)
        self.create_subscription(Twist, 'cmd_vel_can', self.cmd_vel_callback, 10)

        #変数初期化
        self.cmd_vel_transmit_callback_cooldown = 0.01
        self.cmd_vel_transmit_callback_lastCalled = 0.0
        self.cmd_vel_linear_thres = 0.01
        self.cmd_vel_angular_thres = 0.01
        self.last_linear_x = 0.0
        self.last_linear_y = 0.0
        self.last_angular_z = 0.0
    

    def heartbeat_timer_callback(self):
        heartbeat.send_heartbeat(self.canabe_pub)

    def lcu_callback(self, msg):
        self.logger.info(f"Received LCU message: {msg}")
        LCU_controller.LCU_controller(self.canabe_pub, msg.led_mode, msg.led_id, msg.led_color, msg.duration)

    def cmd_vel_callback(self, msg):
        self.logger.info(f"Received cmd_vel message: {msg}")
        cmd_vel_controller.cmd_vel_send(self.canabe_pub, 1, msg.linear.x, msg.linear.y, msg.angular.z)


def main(args = None):
    rclpy.init(args=args)
    node = imrc_canabe_bridge()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

