#!/usr/bin/env pybricks-micropython
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile

# import package that can calculate arctan
from math import atan2, pi


ev3 = EV3Brick()

class Robot_Car:
    def __init__(self):
        self.motor_left = Motor(Port.A)
        self.motor_right = Motor(Port.B)
        self.speed = 200 
        self.location = [0, 0]
        self.orientation = 0 # [0,2pi]
    def relocate(self, x, y):
        self.location = [x, y]
    
    def move_forward(self, length):
        # distance per second = 0.3 * speed
        self.motor_left.run(self.speed)
        self.motor_right.run(self.speed)
        duration = length / (0.3 * self.speed)
        wait(duration)
        self.stop()

    def move_backward(self, length):
        # distance per second = 0.3 * speed
        self.motor_left.run(-self.speed)
        self.motor_right.run(-self.speed)
        duration = length / (0.3 * self.speed)
        wait(duration)
        self.stop()

    def turn_left(self, angle):
        # angle per second = 0.47 * speed
        self.motor_left.run(-self.speed)
        self.motor_right.run(self.speed)
        duration = angle / (0.47 * self.speed)
        wait(duration)
        self.stop()

    def turn_right(self, angle):
        # angle per second = 0.47 * speed
        self.motor_left.run(self.speed)
        self.motor_right.run(-self.speed)
        duration = angle / (0.47 * self.speed)
        wait(duration)
        self.stop()

    def stop(self):
        self.motor_left.stop(Stop.COAST)
        self.motor_right.stop(Stop.COAST)

    def move_to(self, x, y):
        robot_x = self.location[0]
        robot_y = self.location[1]
        robot_orientation = self.orientation

        dx = x - robot_x
        dy = y - robot_y
        angle = atan2(dy, dx) - robot_orientation
        distance = (dx**2 + dy**2)**0.5

        self.turn_left(angle)
        self.move_forward(distance)
        self.location = [x, y]
        self.orientation = atan2(dy, dx)
    

if __name__ == "__main__":
    car = Robot_Car()
    ev3.speaker.beep()  
    car.move_to(0, 100)
    car.move_to(100, 100)
    car.move_to(100, 0)
    car.move_to(0, 0)
    ev3.speaker.beep()


