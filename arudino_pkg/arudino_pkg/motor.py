#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import struct


class MotorSerialNode(Node):
    def __init__(self):
        super().__init__('motor_serial_node')


        # 1. 訂閱經過安全過濾的指令 (從你的安全節點傳來)
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel_safe',
            self.motor_callback,
            10
        )


        # 2. 依照你提供的規格初始化序列埠
        try:
            self.ser = serial.Serial(
                port='/dev/mymotor',  # 請確認此路徑正確
                baudrate=115200,
                bytesize=serial.EIGHTBITS,    # bytesize=8
                parity=serial.PARITY_NONE,    # parity='N'
                stopbits=serial.STOPBITS_ONE, # stopbits=1
                timeout=0.5
            )
            self.get_logger().info("✅ 序列埠已成功啟動 (115200, 8N1)")
        except Exception as e:
            self.get_logger().error(f"❌ 無法開啟序列埠: {e}")


    def calculate_crc(self, data):
        """ Modbus RTU CRC16 計算 (小端序回傳) """
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        # 回傳 2 bytes 的 bytes 物件
        return crc.to_bytes(2, byteorder='little')


    def motor_callback(self, msg: Twist):
        try:
            # A. 提取數據 (v: 前後比率, w: 旋轉比率, max_rpm: 速度上限)
            v = msg.linear.x
            w = msg.angular.z
            max_rpm = - msg.linear.z


            # B. 差速計算 (左右輪 RPM)
            right_rpm = int((v - (w * 0.5)) * max_rpm)
            left_rpm = int((v + (w * 0.5)) * max_rpm)


            # C. 將 RPM 轉為 2-byte 有符號短整數 (大端序)
            # 例如 300 轉為 \x01\x2c
            l_hex = struct.pack('>h', left_rpm)
            r_hex = struct.pack('>h', right_rpm)


            # D. 組裝 15-byte 完整參數指令
            # 這是根據你提供的 num 範例格式，將動態 RPM 填入
            base_cmd = bytearray([
                0x00, 0x65, 0x02, 0x02, # 站號、功能碼、模式
                0x0A,                   # 加速度 (10)
                0x00, 0x00,             # 預留/偏移
                r_hex[0], r_hex[1],     # 左輪轉速 (動態)
                0x01,                   # 第二站號/固定碼
                0x0A,                   # 減速度 (10)
                0x00, 0x00,             # 預留/偏移
                l_hex[0], l_hex[1]      # 右輪轉速 (動態)
            ])


            # E. 計算並附加 CRC16
            full_cmd = base_cmd + self.calculate_crc(base_cmd)


            # F. 發送至馬達
            self.ser.reset_input_buffer()  # 清除舊數據
            self.ser.write(full_cmd)
           
            # 選項：在終端機觀察發送內容 (偵錯用)
            # self.get_logger().info(f"發送: {full_cmd.hex().upper()}")


        except Exception as e:
            self.get_logger().error(f"回調執行錯誤: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = MotorSerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.ser.is_open:
            node.ser.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()