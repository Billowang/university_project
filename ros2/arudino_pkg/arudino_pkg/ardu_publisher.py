#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

class Mynode(Node):

    def timer(self):
        msg = Bool()
        self.state = not self.state
        msg.data = self.state
        self.publisher.publish(msg)
        self.get_logger().info(f"publisher {msg.data} ")
        
    
    def __init__(self):
        super().__init__("ardu")
        self.publisher = self.create_publisher(Bool,"cmd",10)
        self.timerr = self.create_timer(1, self.timer)
        self.state = False


def main(args=None):
    rclpy.init(args = args)
    node = Mynode()
    rclpy.spin(node)
    '''node.destroy_node()'''
    rclpy.shutdown()

if __name__ == "__main__":
    main()
