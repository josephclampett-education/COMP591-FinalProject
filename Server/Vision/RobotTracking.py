class RobotTracking:
    def __init__(self):
        self.robot_position = (0, 0, 0)
        self.orientation = 0
        self.status = "IDLE"

    def update_position(self, x, y, z):
        self.robot_position = (x, y, z)

    def update_orientation(self, angle):
        self.orientation = angle

    def update_status(self, status):
        self.status = status

    def get_location(self):
        return self.robot_location
    
    def get_orientation(self):
        return self.orientation
    
    def get_status(self):
        return self.status