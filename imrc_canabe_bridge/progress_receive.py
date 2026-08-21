from rclpy.publisher import Publisher

from imrc_messages.msg import RobotActionProgress
from imrc_messages.msg import EcanCommand

# /can_rx_demoトピックからどの基板のデータを受け取るか指定し、それの名前を決定
# [unit_code, unit_index, name]
TARGET = [
    [16, 1, "wheel"],
    [16, 2, "injection"],
    [16, 3, "arm"],
    [19, 1, "relay"],
    [20, 1, "lcu"],
    [22, 1, "pcu"],
]

# 送信する値entryの値と、どの動作を命令しているかの対応
INJECTION_ORDER_NUM = {10: "get", 11: "carry", 20: "injection", 21: "preparing"}

# 以下payload_index, entryとparam, stateの対応
TASK = {
    "wheel" : [
        [0, 0, "live", {1: "able", 2: "disable"}],
    ],
    
    "injection" : [
        [3, 0, "send", INJECTION_ORDER_NUM],
        [3, 1, "timeout", INJECTION_ORDER_NUM],
        [3, 2, "error", INJECTION_ORDER_NUM],
        [3, 11, "get"],
        [3, 13, "carry"],
    ],
    
    "arm" : [
        [3, 0, "finish", {1: "keep_success", 2: "catch_success", 3: "gate_success", 
                        11: "keep_fail", 12: "catch_fail", 13: "gate_fail"}],
    ],
    
    "relay" : [
        [3, 1, "send"],
        [3, 2, "open"],
        [3, 3, "close"],
    ],
    
    "lcu" : [
        [0, 0, "live"],
    ],
    
    "pcu" : [
        # [0, 4, "live"],
        [0, 0, "reset"],
    ],
}

class ProgressReceive:
    def __init__(self):
        pass

    @classmethod
    def receive_progress(cls, publisher: Publisher, subscription: EcanCommand):
        # 送られてきた基板の名前を照合
        for target in TARGET:
            if subscription.unit_code == target[0] and subscription.unit_index == target[1]:
                # その基板でpubする必要のあるタスク表を取得
                tasks = TASK[target[2]]
                for i in tasks:
                    # このifに入ったらデータをpubする必要がある（それ以外でしてはいけない）
                    if i[0] == subscription.payload_index and i[1] == subscription.payload_entry:
                        msg = RobotActionProgress()
                        msg.target = target[2]
                        msg.param = i[2]
                        if len(i) == 4 and len(subscription.data) > 0:
                            msg.state = i[3].get(subscription.data[0], "unknown")
                        else:
                            msg.state = "success"
                        publisher.publish(msg)
                        break
                break