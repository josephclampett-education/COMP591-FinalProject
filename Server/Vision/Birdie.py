import cv2
from Server.Location import BirdieLocation

class Birdie(BirdieLocation):
    def __init__(self, id, x, y, z, hit_ground, bounding_rect, contour):
        self.id = id
        self.bounding_rect = bounding_rect  # (x, y, w, h)
        self.contour = contour
        super().__init__(x, y, z, self.calculate_orientation(), hit_ground)
        self.history = [(x, y, z)]  # Initialize with the current position

    def update(self, x, y, z, bounding_rect, contour):
        self.x = x
        self.y = y
        self.z = z
        self.bounding_rect = bounding_rect
        self.contour = contour
        self.angle = self.calculate_orientation()
        self.history.append((x, y, z))  # Append the new position to history

        # TODO implement check that sets hit_ground to true if z = floor
        if self.z == 0: # Take the z value from aruco marker court
            self.hit_ground = True

    def calculate_orientation(self):
        # Calculate the orientation using the contour
        rect = cv2.minAreaRect(self.contour)
        angle = rect[2]
        return angle