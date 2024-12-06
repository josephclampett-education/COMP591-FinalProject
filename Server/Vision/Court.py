import numpy as np
from Server.Location import CourtLocation, BirdieLocation

WIDTH = 5.18 / 2  # in meters
LENGTH = 13.4 / 2  # in meters
MIDDLE_TO_SERVEZONE = 1.98 # in meters

SCALE = 10

class Court(CourtLocation):
    def __init__(self, aruco_corners):
        CourtLocation.__init__(self, aruco_corners)

    def is_inside(self, birdie: BirdieLocation):
        """
        Check if a birdie is inside the court.

        Parameters:
        birdie_pos (tuple): A tuple with the (x, y, z) coordinates of the birdie.

        Returns:
        bool: True if the birdie is inside the court, False otherwise.
        """
        court_2d = [(x, y) for x, y, _ in zip(self.A, self.B, self.C, self.D)]
        birdie_2d = [birdie.x, birdie.y]

        inside = True
        for i in range(4):
            o = court_2d[i]
            a = court_2d[(i + 1) % 4]
            if self.cross(o, a, birdie_2d) < 0:
                inside = False
                break

        return inside


    def which_side(self, birdie: BirdieLocation):
        """
        Check if the birdie is on the left or right side of the court.
        """
        # TODO 


    def display_court(self):
        """
        Display the court's corner coordinates.
        """
        # TODO 
        print("Court Corners:")
        for i, corner in enumerate(self.court_corners):
            print(f"Corner {i + 1}: {corner}")
    
    
    def cross(o, a, b):
        """Helper function to calculate the cross product of vectors OA and OB."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

# Executable part
if __name__ == "__main__":
    # Define court corners and birdie position
    court_corners = [(0, 0, 0), (10, 0, 0), (10, 5, 0), (0, 5, 0)]
    birdie_pos = (5, 2, 0)

    # Create an instance of BirdieCourt
    court = Court(court_corners)

    # Display the court corners
    court.display_court()

    # Check if the birdie is inside the court
    if court.is_inside(birdie_pos):
        print("The birdie is inside the court.")
    else:
        print("The birdie is outside the court.")
    
    
