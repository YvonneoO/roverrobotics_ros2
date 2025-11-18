#!/usr/bin/env python3
import argparse
import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo


class ImagePublisher(Node):
    def __init__(self, args):
        super().__init__('image_publisher')
        self.args = args
        self.bridge = CvBridge()
        self.capture_count = 0

        if self.args.show:
            cv2.namedWindow('video', cv2.WINDOW_NORMAL)

        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/camera/camera_info', 10)

        self.cap = cv2.VideoCapture(self.args.input)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2880)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)

        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera at index {self.args.input}")

        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        backend = self.cap.getBackendName()

        info_msg = (
            f"Camera opened successfully:\n"
            f"  Device: /dev/video{self.args.input}\n"
            f"  Backend: {backend}\n"
            f"  Resolution: {self.actual_width}x{self.actual_height}\n"
            f"  FPS: {self.fps}"
        )
        self.get_logger().info(info_msg)

        self.camera_info = CameraInfo()
        self.camera_info.header.frame_id = "camera_frame"
        self.camera_info.width = self.actual_width
        self.camera_info.height = self.actual_height

        timer_period = 1.0 / self.fps if self.fps and self.fps > 0 else 0.033
        self.timer = self.create_timer(timer_period, self.publish_frame)

    def publish_frame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.get_logger().error("Failed to read frame from camera")
                return

            timestamp = self.get_clock().now().to_msg()
            ros_image = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            ros_image.header.stamp = timestamp
            ros_image.header.frame_id = "camera_frame"
            self.image_pub.publish(ros_image)

            self.camera_info.header.stamp = timestamp
            self.camera_info_pub.publish(self.camera_info)

            if self.args.show:
                cv2.imshow('video', frame)
                key = cv2.waitKey(1)  # type: ignore[attr-defined]
                if key == 27:
                    self.get_logger().info("ESC pressed, shutting down image publisher.")
                    rclpy.shutdown()
        except (ValueError, RuntimeError) as exc:
            self.get_logger().error(f"Failed to publish image/camera_info: {exc}")
            return

        self.capture_count += 1

    def cleanup(self):
        if self.cap is not None:
            self.cap.release()
        if self.args.show:
            cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Camera Image Publisher for ROS 2')
    parser.add_argument('-i', '--input', help='Camera Number', type=int, default=0)
    parser.add_argument('--show', action='store_true', help='Show OpenCV window (needs X forwarding).')

    args, ros_args = parser.parse_known_args()
    rclpy.init(args=ros_args)

    image_publisher = ImagePublisher(args)

    try:
        rclpy.spin(image_publisher)
    except KeyboardInterrupt:
        image_publisher.get_logger().info("Keyboard interrupt received, shutting down.")
    finally:
        image_publisher.cleanup()
        image_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
