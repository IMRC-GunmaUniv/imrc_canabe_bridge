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
from imrc_messages.msg import RU
from imrc_messages.msg import PCU
from imrc_messages.msg import EcanCommand

from imrc_canabe_bridge.LCU_controller import *
from imrc_canabe_bridge.heartbeat import *
from imrc_canabe_bridge.RU_controller import *
from imrc_canabe_bridge.PCU_controller import *
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
        self.create_subscription(EcanCommand, 'can_rx_demo', self.eCAN_callback, 10)


        self.create_subscription(LCU, 'lcu', self.lcu_callback, 10)
        self.create_subscription(Twist, 'cmd_vel_can', self.cmd_vel_can_callback, 10)
        self.create_subscription(RU, 'ru', self.ru_callback, 10)
        self.create_subscription(PCU, 'pcu', self.pcu_callback, 10)

        self.lcu_ctrl = LCU_controller(self)
        self.ru_ctrl = RU_controller(self)
        self.pcu_ctrl = PCU_controller(self)
        self.cmd_vel_ctrl = cmd_vel_controller(self)

    #-------受信-------
    def eCAN_callback(self, msg):
        self.logger.info(f"Received eCAN message: {msg}")

    
    #-------送信-------
    def heartbeat_timer_callback(self): #生存信号
        heartbeat.send_heartbeat(self.canabe_pub)

    def lcu_callback(self, msg):    #LCU
        self.logger.info(f"Received LCU message: {msg}")
        self.lcu_ctrl.LCU_control(self.canabe_pub, msg.led_mode, msg.led_id, msg.led_color, msg.duration)

    def cmd_vel_can_callback(self, msg):    #cmd_vel_CAN
        self.logger.info(f"Received cmd_vel message: {msg}")
        self.cmd_vel_ctrl.cmd_vel_send(self.canabe_pub, 1, msg.linear.x, msg.linear.y, msg.angular.z)

    def ru_callback(self, msg):    #RU
        self.logger.info(f"Received RU message: {msg}")

        if(msg.mode == "normal"):
            self.ru_ctrl.RU_control(self.canabe_pub, msg.unit_index, msg.relay_no, msg.relay_state)
        elif(msg.mode == "absolute"):
            self.ru_ctrl.RU_absolute_control(self.canabe_pub, msg.unit_index, msg.relay_no, msg.relay_state)
        else:
            self.logger.error(f"Invalid mode received in RU message: {msg.mode}")

    def pcu_callback(self, msg):    #PCU
        self.logger.info(f"Received PCU message: {msg}")

        if(msg.mode == "normal"):
            self.pcu_ctrl.PCU_control(self.canabe_pub, msg.unit_index, msg.relay_state)
        elif(msg.mode == "absolute"):
            self.pcu_ctrl.PCU_absolute_control(self.canabe_pub, msg.unit_index, msg.relay_state)
        else:
            self.logger.error(f"Invalid mode received in PCU message: {msg.mode}")


def main(args = None):
    rclpy.init(args=args)
    node = imrc_canabe_bridge()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

