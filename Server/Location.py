import math
import numpy as np

class Position:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __sub__(self, other):
        return Position(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
            )

    def __str__(self):
        return f"{self.x}, {self.y}, {self.z}"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (self.x, self.y, self.z) == (other.x, other.y, other.z)

    # Returns the angle bewteen two Positions in radians
    def angle_between(self, other):
        temp = other - self
        return math.atan2(temp.y, temp.x)

class Orientation:
    # angle in radians
    def __init__(self, angle):
        self.angle = angle

class BirdieLocation(Position, Orientation):
    _birdie_length = 5 # TODO
    _birdie_width = 2 # TODO

    def __init__(self, x, y, z, angle, hit_ground):
        Position.__init__(self, x, y, z)
        Orientation.__init__(self, angle)
        self.hit_ground = hit_ground


class RobotLocation(Position, Orientation):
    _grabber_length = 30 # TODO
    center_to_grabber_tip = 50 # TODO
    grabber_angle = math.radians(25) # TODO

    def __init__(self, x, y, z, angle):
        Position.__init__(self, x, y, z)
        Orientation.__init__(self, angle)

    def get_grabber_position(self):
        return Position(
            self.x + self._grabber_length * math.cos(self.angle),
            self.y + self._grabber_length * math.sin(self.angle),
            self.z
            )
    

class CourtLocation():
    WIDTH = 6.1  # in meters
    LENGTH = 13.4  # in meters
    SCALE = 10

    def __init__(self, aruco_corners):
        self.A, self.B, self.C, self.D = self.calculate_court_corners(aruco_corners)
        

    def calculate_court_corners(self, aruco_corners):
        """
        Calculate the court corners based on the ArUco corners.
        """

        cornerA = aruco_corners[0]
        cornerB = aruco_corners[1]
        cornerC = aruco_corners[2]
        cornerD = aruco_corners[3]

        # Find the vectors DA and DC and normalize them to a scale of 1
        dDA_x = cornerA[0] - cornerD[0]
        dDA_y = cornerA[1] - cornerD[1]

        vDA_norm = np.linalg.norm([dDA_x, dDA_y])
        vDA = np.array([dDA_x, dDA_y, 0]) / vDA_norm

        dDC_x = cornerC[0] - cornerD[0]
        dDC_y = cornerC[1] - cornerD[1]
        vDC_norm = np.linalg.norm([dDC_x, dDC_y])
        vDC = np.array([dDC_x, dDC_y, 0]) / vDC_norm

        # Calculate the court corners
        court_cornerD = cornerD
        print(vDA)
        print(court_cornerD)
        court_cornerA = (self.SCALE * self.WIDTH * vDA) + court_cornerD
        court_cornerC = (self.SCALE * self.LENGTH * vDC) + court_cornerD
        court_cornerB = court_cornerA + court_cornerC - court_cornerD
        
        court_cornerA = Position.__init__(*court_cornerA, 0)
        court_cornerB = Position.__init__(*court_cornerB, 0)
        court_cornerC = Position.__init__(*court_cornerC, 0)
        court_cornerD = Position.__init__(*court_cornerD, 0)

        return court_cornerA, court_cornerB, court_cornerC, court_cornerD
    