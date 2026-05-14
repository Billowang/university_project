#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
import math


class lidardistance(Node):
    def __init__(self):
        super().__init__("lidar_node")

        self.safe_distance = 0.5
        self.last_cmd = True
        
        self.sub = self.create_subscription(
            LaserScan,
            "/scan",
            self.callback,
            10
        )

        self.pub = self.create_publisher(
            Bool,
            "/distance",
            10
        )
        self.get_logger().info("hi")
    
    def callback(self, msg :LaserScan):
        
        start = True

        for i, distance in enumerate(msg.ranges):

            if math.isinf(distance) or math.isnan(distance):
                continue
        
            angle = msg.angle_min + i * msg.angle_increment

            if -1.91 <= angle <= -1.22:

                if distance < self.safe_distance:
                    start = False
                    break
        
        cmd_msg = Bool()
        cmd_msg.data = start
        
        if cmd_msg != self.last_cmd:
            self.pub.publish(cmd_msg)
            self.last_cmd = cmd_msg



def main(args=None):
    rclpy.init(args = args)
    node =lidardistance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()