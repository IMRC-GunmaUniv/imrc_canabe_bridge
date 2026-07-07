#!/usr/bin/env python3
from imrc_messages.msg import EcanCommand
from rclpy.publisher import Publisher
from rclpy.node import Node

class PCU_controller:
    def __init__(self, node: Node):  # 【修正】呼び出し元から node を受け取る
        """
        初期化関数
        :param node: 呼び出し元のROS 2ノード（ロガーや時間管理の参照用）
        """
        self.node = node  # 【修正】インスタンス変数に保存する
        self.pre_state = -1  # 前回の状態（初期値は未定状態の-1）
        self.state = 0
        self.voltage_state = 0

    def _pcu_relay_transmit_internal(self, publisher: Publisher, unit_index: int, relay_state: int):
        """内部関数: 実際にROS 2メッセージを構築してパブリッシュする"""
        
        # ROS 2の標準ロガーを使用してログ出力
        if relay_state == 0:
            self.node.get_logger().info("PCU_voltage_cutoff")
        elif relay_state == 1:
            self.node.get_logger().info("PCU_voltage_recovery")

        # ROS 2 メッセージ（EcanCommand）の作成と送信
        msg = EcanCommand()
        msg.unit_code = 22
        msg.unit_index = unit_index
        msg.payload_index = 3
        msg.payload_entry = 0
        msg.data = [int(relay_state)]  # uint8の配列（Pythonではリスト）に格納
        
        publisher.publish(msg)

    def _pcu_relay_control(self, publisher: Publisher, unit_index: int, relay_state: int):
        """通常のリレー制御（状態が変化したときのみ送信）"""
        if relay_state != self.pre_state:
            self.pre_state = relay_state  # 前回の状態を更新
            self._pcu_relay_transmit_internal(publisher, unit_index, relay_state)

    def PCU_absolute_control(self, publisher: Publisher, unit_index: int, relay_state: int):
        """絶対リレー制御（状態の変化に関わらず、強制的に最新状態を送信）"""
        self.pre_state = relay_state  # 状態を同期
        self._pcu_relay_transmit_internal(publisher, unit_index, relay_state)

    def PCU_control(self, publisher: Publisher, unit_index: int, relay_state: int):
        """PCU制御のエントリーポイント（外部から呼ばれるメイン関数）"""
        if relay_state == 0:
            self._pcu_voltage_cutoff(publisher, unit_index)
        elif relay_state == 1:
            self._pcu_voltage_recovery(publisher, unit_index)  
        else:
            self.node.get_logger().error(f"Invalid relay_state received: {relay_state}")

    def _pcu_voltage_cutoff(self, publisher: Publisher, unit_index: int):
        """電圧遮断要求（内部処理）"""
        self.state = 0
        self._pcu_relay_control(publisher, unit_index, self.state)

    def _pcu_voltage_recovery(self, publisher: Publisher, unit_index: int):
        """電圧復帰要求（内部処理）"""
        self.state = 1
        self._pcu_relay_control(publisher, unit_index, self.state)