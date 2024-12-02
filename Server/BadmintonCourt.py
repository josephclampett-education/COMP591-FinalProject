import numpy as np

WIDTH = 6.1  # in meters
LENGTH = 13.4  # in meters
SCALE = 10

class BadmintonCourt:
    def __init__(self, aruco_corners):
        """
        Initialize the BirdieCourt class with the court corners.

        Parameters:
        court_corners (list of tuple): A list of four tuples representing the court corners' (x, y, z) coordinates.
        """
        self.court_corners = self.calculate_court_corners(aruco_corners)

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
        court_cornerA = (SCALE * WIDTH * vDA) + court_cornerD
        court_cornerC = (SCALE * LENGTH * vDC) + court_cornerD
        court_cornerB = court_cornerA + court_cornerC - court_cornerD

        return np.array([court_cornerA, court_cornerB, court_cornerC, court_cornerD])
    

    def is_inside(self, birdie_pos):
        """
        Check if a birdie is inside the court.

        Parameters:
        birdie_pos (tuple): A tuple with the (x, y, z) coordinates of the birdie.

        Returns:
        bool: True if the birdie is inside the court, False otherwise.
        """
        court_2d = [(x, y) for x, y, z in self.court_corners]
        birdie_2d = birdie_pos[:2]

        def cross(o, a, b):
            """Helper function to calculate the cross product of vectors OA and OB."""
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        inside = True
        for i in range(4):
            o = court_2d[i]
            a = court_2d[(i + 1) % 4]
            if cross(o, a, birdie_2d) < 0:
                inside = False
                break

        return inside

    def which_side(self, birdie_pos):
        """
        Check if the birdie is on the left or right side of the court.
        """


    def display_court(self):
        """
        Display the court's corner coordinates.
        """
        print("Court Corners:")
        for i, corner in enumerate(self.court_corners):
            print(f"Corner {i + 1}: {corner}")

    def aruco_board_mapping_new(cornerset):
    
        width = 6.1  # in meters
        length = 13.4  # in meters
        scale = 10

        cornerA = cornerset[0]
        cornerB = cornerset[1]
        cornerC = cornerset[2]
        cornerD = cornerset[3]

        dDA_x = cornerA[0] - cornerD[0]
        dDA_y = cornerA[1] - cornerD[1]

        vDA_norm = np.linalg.norm([dDA_x, dDA_y])
        vDA = np.array([dDA_x, dDA_y]) / vDA_norm

        dDC_x = cornerC[0] - cornerD[0]
        dDC_y = cornerC[1] - cornerD[1]
        vDC_norm = np.linalg.norm([dDC_x, dDC_y])
        vDC = np.array([dDC_x, dDC_y]) / vDC_norm



        court_cornerD = cornerD
        court_cornerA = (scale * width * vDA) + court_cornerD
        court_cornerC = (scale * length * vDC) + court_cornerD
        court_cornerB = court_cornerA + court_cornerC - court_cornerD

        return np.array([court_cornerA, court_cornerB, court_cornerC, court_cornerD])
        

    def aruco_board_mapping(cornerset):
        cornerA = cornerset[0]
        cornerB = cornerset[1]
        cornerC = cornerset[2]
        cornerD = cornerset[3]

        v1 = cornerD - cornerA
        v2 = cornerB - cornerA
        

        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)
        # Create a matrix with both vectors spanning the field
        A = np.array([v1, v2])
        A_orth = A
        # TODO Adding this makes the mapping flip at some point so we wont use it for now.
        #A_orth = np.linalg.svd(A)[0]
        
        A_hat = np.eye(3)  # Create a 3x3 identity matrix
        A_hat[:2, :2] = A_orth  # Set the rotation part
        A_hat[:2, 2] = cornerA  # Set the translation part


        # Define local coordinates of the corners
        width = 6.1  # in meters
        length = 13.4  # in meters
        scale = 10
        local_corners = np.array([
            [0, 0],         # CornerA (marker corner)
            [scale*width, 0],     # CornerB (along the width)
            [0, scale*length],    # CornerC (along the length)
            [scale*width, scale*length] # CornerD (diagonal)
        ])

        # Convert to homogeneous coordinates
        local_corners_hom = np.hstack([local_corners, np.ones((4, 1))])  # Add 1 for homogeneous

        # Apply transformation matrix
        court_corners_RS_hom = (A_hat @ local_corners_hom.T).T

        # Extract global coordinates
        court_corners_RS = court_corners_RS_hom[:, :2]  # Drop the homogeneous part

        return court_corners_RS

    def is_birdie_in_court(court_corners_RS, birdie_pos_RS):
        # Project 3D coordinates to 2D (ignoring z-axis for planar court detection)
        court_2d = [(x, y) for x, y, z in court_corners_RS]
        birdie_2d = birdie_pos_RS[:2]

        # Calculate the cross product of vectors to determine if the point is inside
        def cross(o, a, b):
            """Helper function to calculate the cross product of vectors OA and OB."""
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        # Check if the birdie is on the same side for all edges
        inside = True
        for i in range(4):
            o = court_2d[i]
            a = court_2d[(i + 1) % 4]
            if cross(o, a, birdie_2d) < 0:
                inside = False
                break

        return inside

# Executable part
if __name__ == "__main__":
    # Define court corners and birdie position
    court_corners = [(0, 0, 0), (10, 0, 0), (10, 5, 0), (0, 5, 0)]
    birdie_pos = (5, 2, 0)

    # Create an instance of BirdieCourt
    court = BadmintonCourt(court_corners)

    # Display the court corners
    court.display_court()

    # Check if the birdie is inside the court
    if court.is_inside(birdie_pos):
        print("The birdie is inside the court.")
    else:
        print("The birdie is outside the court.")
