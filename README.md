# imrc_canabe_bridge

ROS 2 のトピック（`LCU` / `RU` / `PCU` / `cmd_vel`）を受け取り、CAN（eCAN）向けの `EcanCommand` メッセージに変換して送信するブリッジノードです。

## 起動方法

```bash
ros2 run imrc_canabe_bridge imrc_canabe_bridge
```

起動すると以下が有効になります。

- `/can_tx_demo` へCANコマンドをpublish
- `can_rx_demo` を購読してログ出力
- `lcu` / `ru` / `pcu` / `cmd_vel_can` を購読し、内容に応じてCANへ変換して送信
- 0.5秒ごとに自動でハートビートを送信（ユーザー操作不要）

---

## LED制御（LCU）

**トピック名:** `lcu`　**型:** `imrc_messages/msg/LCU`

`lcu_callback` は受け取ったメッセージの4つのフィールドをそのまま `LCU_control` に渡します。

| フィールド | 型 | 必要な値 | 説明 |
|---|---|---|---|
| `led_mode` | string | `"set_rgb"` / `"turn_off"` / `"set_blink"` / `"set_bloom"` | 動作モード |
| `led_id` | int | 対象LEDの番号 | どのLEDを操作するか |
| `led_color` | string | `"red"` / `"green"` / `"blue"` | 発光色（この3色のみ対応） |
| `duration` | int | ミリ秒 | 点滅・ブルームの周期（`set_rgb`/`turn_off`時は無視される） |

### モードごとの使い分け

- **常時点灯させたい** → `led_mode: "set_rgb"` ＋ `led_color` を指定（`duration`は不要）
- **消灯したい** → `led_mode: "turn_off"`（`led_color`・`duration`は内部的に無視される。ただし`led_color`は必須フィールドなので何か入れておく）
- **点滅させたい** → `led_mode: "set_blink"` ＋ `led_color` ＋ `duration`（点滅周期）
- **フェードイン/アウトさせたい** → `led_mode: "set_bloom"` ＋ `led_color` ＋ `duration`（変化周期）

### 実行例

```bash
# LED 1番を赤で常時点灯
ros2 topic pub --once /lcu imrc_messages/msg/LCU \
  "{led_mode: 'set_rgb', led_id: 1, led_color: 'red', duration: 0}"

# LED 2番を緑で1秒周期の点滅
ros2 topic pub --once /lcu imrc_messages/msg/LCU \
  "{led_mode: 'set_blink', led_id: 2, led_color: 'green', duration: 1000}"

# LED 1番を消灯
ros2 topic pub --once /lcu imrc_messages/msg/LCU \
  "{led_mode: 'turn_off', led_id: 1, led_color: 'red', duration: 0}"
```

> ⚠️ `led_color` に `red`/`green`/`blue` 以外を入れるとエラーログのみ出力され、その後の色データが未定義のまま処理が進む可能性があります。必ず3色のいずれかを指定してください。

---

## 走行制御（cmd_vel）

**トピック名:** `cmd_vel_can`　**型:** `geometry_msgs/msg/Twist`

一般的な`Twist`メッセージをそのまま使えます。必要なのは以下の3成分のみです。

| フィールド | 必要な値 | 説明 |
|---|---|---|
| `linear.x` | 実数（m/s想定） | 前後方向の速度 |
| `linear.y` | 実数（m/s想定） | 左右方向の速度（メカナム等の横移動用） |
| `angular.z` | 実数（rad/s想定） | 旋回速度（yaw） |

内部で1000倍して整数化し、`-32768〜32767`の範囲にクランプしてから送信するため、極端に大きい値を入れても壊れずクリップされます。`unit_index`は固定で`1`が使われます（呼び出し元で変更不可）。

### 実行例

```bash
# 前進0.5m/s、旋回なし
ros2 topic pub --once /cmd_vel_can geometry_msgs/msg/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

---

## 汎用リレー制御（RU, 4ch）

**トピック名:** `ru`　**型:** `imrc_messages/msg/RU`

| フィールド | 型 | 必要な値 | 説明 |
|---|---|---|---|
| `mode` | string | `"normal"` / `"absolute"` | 制御モード |
| `unit_index` | int | 対象RUユニットの番号 | 複数RUがある場合の識別子 |
| `relay_no` | int | `1`〜`4` | 操作するリレー番号（範囲外はエラー） |
| `relay_state` | int | `0`（OFF）/ `1`（ON） | 設定したい状態 |

### モードの違い（重要）

- **`normal`**：内部で4ch分の状態を保持しており、**前回と変化があったリレーのみ**CANへ送信します（差分送信）。同じ状態を繰り返し送っても再送されません。
- **`absolute`**：状態変化の有無に関わらず、指定したリレーの状態を**毎回強制送信**します。確実に反映させたい／再同期させたい場合に使用します。

### 実行例

```bash
# リレー2番をON（差分送信モード）
ros2 topic pub --once /ru imrc_messages/msg/RU \
  "{mode: 'normal', unit_index: 1, relay_no: 2, relay_state: 1}"

# リレー2番を強制的にOFFへ再送信
ros2 topic pub --once /ru imrc_messages/msg/RU \
  "{mode: 'absolute', unit_index: 1, relay_no: 2, relay_state: 0}"
```

---

## 電源リレー制御（PCU）

**トピック名:** `pcu`　**型:** `imrc_messages/msg/PCU`

| フィールド | 型 | 必要な値 | 説明 |
|---|---|---|---|
| `mode` | string | `"normal"` / `"absolute"` | 制御モード |
| `unit_index` | int | 対象PCUユニットの番号 | 複数PCUがある場合の識別子 |
| `relay_state` | int | `0`（電圧遮断）/ `1`（電圧復帰） | 設定したい状態 |

RUと同様、`normal`は**状態が変化した時のみ**送信、`absolute`は**毎回強制送信**します。`relay_state`が0/1以外の場合はエラーログのみでCAN送信されません。

### 実行例

```bash
# 電源を遮断（差分送信モード）
ros2 topic pub --once /pcu imrc_messages/msg/PCU \
  "{mode: 'normal', unit_index: 1, relay_state: 0}"

# 電源を強制的に復帰
ros2 topic pub --once /pcu imrc_messages/msg/PCU \
  "{mode: 'absolute', unit_index: 1, relay_state: 1}"
```

---

## ハートビート

**操作不要。** ノード起動と同時に0.5秒周期で自動送信されます（`unit_code=2`, `data=[1]`固定）。ユーザーがトピックをpublishする必要はありません。

---

## USBデバイスのシリアル番号からポートを特定したい場合

CANアダプタ等、`/dev/ttyACM0`のような番号が接続順で変わってしまう場合に `serial_resolver.py` を使ってシリアル番号から固定的にパスを取得できます。

```python
from imrc_canabe_bridge.serial_resolver import get_tty_by_serial, display_device_list

# 接続中の全デバイスとシリアル番号を確認したい時
display_device_list()

# 既知のシリアル番号からデバイスパスを取得
port = get_tty_by_serial("XXXXXXXX")
```

`udevadm` コマンド（`/bin/udevadm`）が使える環境が前提です。

---

## トピック一覧まとめ

| トピック名 | 型 | 用途 | unit_code |
|---|---|---|---|
| `lcu` | `imrc_messages/msg/LCU` | LED制御 | 20 |
| `cmd_vel_can` | `geometry_msgs/msg/Twist` | 走行制御 | 16 |
| `ru` | `imrc_messages/msg/RU` | 汎用リレー制御（4ch） | 19 |
| `pcu` | `imrc_messages/msg/PCU` | 電源リレー制御 | 22 |
| `can_rx_demo` | `imrc_messages/msg/EcanCommand` | CAN受信（ログのみ） | - |
| （自動） | - | ハートビート | 2 |

## 既知の注意点

- LCUの`led_color`に不正な文字列を渡すとエラーログ後もそのまま処理が続行され、想定外の動作になる可能性があります。必ず`red`/`green`/`blue`のいずれかを指定してください。
- RU/PCUの`normal`モードは前回状態との差分でしか送信しないため、ノード再起動直後や通信途絶からの復帰直後は`absolute`モードで一度状態を確定させることを推奨します。