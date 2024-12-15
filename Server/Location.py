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

    def get_pos(self):
        return [float(self.x), float(self.y), float(self.z)]

    def is_close(self, other):
        diff = self - other
        return math.sqrt(diff.x**2 + diff.y**2 + diff.z**2) < 20 # TODO: threshold

    def flat_distance(self, other):
        diff = self - other
        return math.sqrt(diff.x**2 + diff.y**2 )

    def get_other_position(self, angle, distance):
        return Position(self.x + math.cos(angle) * distance, self.y + math.sin(angle) * distance, self.z)

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
    center_to_grabber_tip = 160 # TODO
    grabber_angle = math.radians(40) # TODO

    def __init__(self, x, y, z, angle):
        Position.__init__(self, x, y, z)
        Orientation.__init__(self, angle)

    def update(self, x, y, z, angle):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle

    def get_grabber_position(self):
        return Position(
            self.x + self._grabber_length * math.cos(self.angle),
            self.y + self._grabber_length * math.sin(self.angle),
            self.z
            )

    # returns the angle the robot has to turn to face other
    def angle_to(self, other):
        bearingVector = other - self
        bearingAngle = math.atan2(bearingVector.y, bearingVector.x)

        deltaAngle = bearingAngle - self.angle

        if deltaAngle > math.pi:
            deltaAngle -= 2 * math.pi
        if deltaAngle < -math.pi:
            deltaAngle += 2 * math.pi

        return deltaAngle


class CourtLocation():
    WIDTH = 5.18  # in meters
    LENGTH = 13.4 / 2  # in meters
    MIDDLE_TO_SERVEZONE = 1.98 # in meters

    SCALE = 130

    def set_corners(self, aruco_corners=None, court_corners=None):
        if aruco_corners is not None:
            self.CL, self.CR, self.STL, self.STM, self.STR, self.SBR, self.SBM, self.SBL = self.calculate_court_corners(aruco_corners)
        elif court_corners is not None:
            self.CL, self.CR, self.STL, self.STM, self.STR, self.SBR, self.SBM, self.SBL = [Position(*corner) for corner in court_corners]
        else:
            raise Exception("ERROR: Court has to be initialized either with aruco_corners or court_corners!")

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
        vDA = np.array([dDA_x, dDA_y]) / vDA_norm

        dDC_x = cornerC[0] - cornerD[0]
        dDC_y = cornerC[1] - cornerD[1]
        vDC_norm = np.linalg.norm([dDC_x, dDC_y])
        vDC = np.array([dDC_x, dDC_y]) / vDC_norm

        # Calculate the court corners

        # bottom right net
        court_cornerR = cornerD

        # bottom left net
        court_cornerL = (self.SCALE * self.WIDTH * vDA) + court_cornerR

        # top right serve zone
        serve_cornerTR = (self.SCALE * self.LENGTH * vDC) + court_cornerR

        # top left serve zone
        serve_cornerTL = court_cornerL + serve_cornerTR - court_cornerR

        # top middle serve zone
        serve_cornerTM = self.calculate_midpoint2d(serve_cornerTR, serve_cornerTL)

        # right bottom serve zone
        serve_cornerBR = (self.SCALE * self.MIDDLE_TO_SERVEZONE * vDC) + court_cornerR

        # left bottom serve zone
        serve_cornerBL = (self.SCALE * self.MIDDLE_TO_SERVEZONE * vDC) + court_cornerL

        # middle bottom serve zone
        serve_cornerBM = self.calculate_midpoint2d(serve_cornerBL, serve_cornerBR)

        court_cornerL = Position(*court_cornerL, 0)
        court_cornerR = Position(*court_cornerR, 0)
        serve_cornerTL = Position(*serve_cornerTL, 0)
        serve_cornerTM = Position(*serve_cornerTM, 0)
        serve_cornerTR = Position(*serve_cornerTR, 0)
        serve_cornerBR = Position(*serve_cornerBR, 0)
        serve_cornerBM = Position(*serve_cornerBM, 0)
        serve_cornerBL = Position(*serve_cornerBL, 0)

        return court_cornerL, court_cornerR, serve_cornerTL, serve_cornerTM, serve_cornerTR, serve_cornerBR, serve_cornerBM, serve_cornerBL

    def calculate_midpoint2d(self, point1, point2):
        x1, y1, = point1
        x2, y2 = point2
        midpoint = ((x1 + x2) / 2, (y1 + y2) / 2)
        return midpoint
