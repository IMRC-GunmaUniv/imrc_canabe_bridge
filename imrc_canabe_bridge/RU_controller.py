#!/usr/bin/env python3
from imrc_messages.msg import EcanCommand
from rclpy.publisher import Publisher
import rclpy
from rclpy.node import Node
import time

class RU_controller:
    def __init__(self, node: Node): 
        self.node = node
        # 4つのリレー状態を管理するリスト (0: OFF, 1: ON)
        self.relay_state = [0, 0, 0, 0]
        self.pre_relay_state = [-1, -1, -1, -1]  # 初期値を-1にして確実に初回同期させる
        
        # トグル制御用の内部状態管理（リレーインデックスごとの時間と状態）
        self.toggle_states = {
            i: {"last_tick": 0.0, "state": 0} for i in range(4)
        }

    def _ru_relay_transmit_internal(self, publisher, unit_index: int, relay_idx: int, state: int):
        """内部関数: 実際に1つのリレーのCANパケット（ROS 2メッセージ）を構築して送信"""
        msg = EcanCommand()
        msg.unit_code = 19            # RUのunit_codeは19
        msg.unit_index = unit_index
        msg.payload_index = 3         # cmd
        msg.payload_entry = 0         # priority
        
        # リレー番号は 1〜4 に変換して送信
        msg.data = [relay_idx , int(state)]
        
        publisher.publish(msg)
        self.node.get_logger().info(f"RU Relay {relay_idx + 1}: {int(state)}")

    def RU_control(self, publisher, unit_index: int, relay_idx: int, state: int):
        """通常制御: 状態が変化したリレーのみパケットを送信"""
        if not (1 <= relay_idx <= 4):
            self.node.get_logger().error(f"Invalid relay index: {relay_idx}")
            return False

        # 状態配列を更新
        self.relay_state[relay_idx - 1] = state

        # 4つのリレー全ての状態をチェックして、変化があれば送信
        for i in range(4):
            if self.relay_state[i] != self.pre_relay_state[i]:
                self._ru_relay_transmit_internal(publisher, unit_index, i+1, self.relay_state[i])
                self.pre_relay_state[i] = self.relay_state[i]
                self.node.get_logger().info(f"RU Relay {i + 1} state changed to: {self.relay_state[i]}")
        
        return True

    def RU_absolute_control(self, publisher, unit_index: int, relay_idx: int, state: int):
        """絶対制御: 状態変化に関わらず、指定されたリレーの状態を強制送信"""
        if not (1 <= relay_idx <= 4):
            self.node.get_logger().error(f"Invalid relay index: {relay_idx}")
            return False

        self.relay_state[relay_idx - 1] = state
        self.pre_relay_state[relay_idx - 1] = state  # 履歴を同期

        self._ru_relay_transmit_internal(publisher, unit_index, relay_idx , state)
        return True