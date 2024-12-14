import cv2
from Server.Location import BirdieLocation

class Birdie(BirdieLocation):
    def __init__(self, x, y, z, hit_ground, bounding_rect, contour):
        self.bounding_rect = bounding_rect  # (x, y, w, h)
        self.contour = contour
        super().__init__(x, y, z, self.calculate_orientation(), hit_ground)
        self.history = [(x, y, z)]  # Initialize with the current position
        self.trajectory = None # Can be 'left2left', 'left2right', 'right2right', 'right2left'

    def update(self, x, y, z, bounding_rect, contour, court_z):
        if self.hit_ground:
            # Do not update the position if the birdie has hit the ground
            return

        self.x = x
        self.y = y
        self.z = z
        self.bounding_rect = bounding_rect
        self.contour = contour
        self.angle = self.calculate_orientation()
        self.history.append((x, y, z))  # Append the new position to history

        # TODO implement check that sets hit_ground to true if z = floor
        if self.z >= court_z*0.9 : # Take the z value from aruco marker court
            print("Birdie hit ground.")
            self.hit_ground = True

    def calculate_orientation(self):
        # Calculate the orientation using the contour
        rect = cv2.minAreaRect(self.contour)
        angle = rect[2]
        return angle

    def calculate_x_trajectory(self):
        # Calculate the trajectory based on the history
        if len(self.history) < 2:
            print("ERROR: Not enough history points to calculate trajectory")
            return None

        # Calculate the average moving x direction
        delta_x = 0
        for i in range(len(self.history)-1):
            x1 = self.history[i][1] # older datapoint
            x2 = self.history[i+1][1] # newer datapoint
            delta_x += x2 - x1

        return delta_x