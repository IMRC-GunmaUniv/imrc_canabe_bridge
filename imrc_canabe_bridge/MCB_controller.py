#!/usr/bin/env python3
from imrc_messages.msg import EcanCommand
from rclpy.publisher import Publisher
from rclpy.node import Node

class cmd_vel_controller:
    def __init__(self, node: Node): 
        self.node = node 

    @classmethod
    def cmd_vel_send(cls, publisher: Publisher, unit_index: int, x: float, y: float, yaw: float):
        x = int(x * 100)
        y = int(y * 100)
        yaw = int(yaw * 100)

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

TARGET = [
    [2, "belt"],
    [2, "injection"],
    [3, "arm"],
]

TASK = {
    "belt": [
        [3, 10, "tore"],
        [3, 12, "hakobe"],
    ],
    
    "injection": [
        [3, 20, "injection"]
    ],

    "arm": [
        [3,0,"tore"],
        [3,0,"hozi"],
        [3,0,"setti"]

    ]
}

DATA = {#[0] TARGET [1]TASK
    "belt": {
        "hakobe": [0],
        "tore": [0]
    },

    "injection": {
        "injection": lambda val: [
            # (val * 2) >> 8 & 0xFF,  # 1つ目の値（上位バイト）
            # (val * 2) & 0xFF        # 2つ目の値（下位バイト）
            val // 1000,  # 1つ目の値（上位バイト）
            val % 1000 // 10,   # 2つ目の値（下位バイト）
        ]
    },

    "arm": {
        "tore":[1],
        "hozi":[2],
        "setti":[3]
    }
}

class actuater_controller:
    def __init__(self, node: Node): 
        self.node = node 

    @classmethod
    def actuater_send(cls, publisher: Publisher, target_name: str, task_name: str, value: int):
        # TARGETからユニットインデックスを取得
        unit_index = None
        for targets in TARGET:
            if targets[1] == target_name:
                unit_index = targets[0]
                break
        
        if unit_index is None:
            print("TARGET NOT FOUND")
            return


        # TASKからペイロードインデックスとエントリを取得
        payload_index = None
        payload_entry = None
        for category, tasks in TASK.items():
            for task in tasks:
                if task[2] == task_name:
                    payload_index = task[0]
                    payload_entry = task[1]
                    break
            if payload_index is not None:
                break
        
        if payload_index is None:
            print("TASK NOT FOUND")
            return

        #DATAからdataを作成
        if target_name in DATA and task_name in DATA[target_name]:
            formula = DATA[target_name][task_name]
            # DATA内の計算式を実行
            calculated = formula(value) if callable(formula) else formula
            
            # リスト（複数データ）で返ってきた場合、そのまま展開または代入
            if isinstance(calculated, list):
                data = [item & 0xFF for item in calculated]

            else:
                # 単一の数値の場合
                data = [calculated & 0xFF, 0, 0, 0]
        else:
            data = [0]

        # メッセージの作成と送信
        msg = EcanCommand()
        msg.unit_code = 16
        msg.unit_index = unit_index
        msg.payload_index = payload_index
        msg.payload_entry = payload_entry
        msg.data = data  

        publisher.publish(msg)