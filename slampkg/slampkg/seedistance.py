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
        
        front_min =math.radians(-110)
        front_max =math.radians(-70)
        

        min_dist = float('inf')

        step_deg = 3.0
        step_rad = math.radians(step_deg)

        angle = msg.angle_min
        angle_max = msg.angle_max

        print("-----------------")

        while angle <= angle_max:
            index = int(round((angle-msg.angle_min)/msg.angle_increment))

            if index < 0 or index >= len(msg.ranges):
                angle += step_rad
                continue

            dist = msg.ranges[index]

            if dist == 0.0 or math.isinf(dist):
                angle += step_rad
                continue

            if front_min <= angle <= front_max:
        
                min_dist = min(min_dist, dist)

            angle += step_rad
        
        stop_msg = Bool()
        if min_dist < self.safe_distance:
            stop_msg.data = False
            self.get_logger().info("too close")
        else:
            stop_msg.data = True
            self.get_logger().info("fine")
        
        self.pub.publish(stop_msg)



def main(args=None):
    rclpy.init(args = args)
    node =lidardistance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main() 