import select
import json
import pyrealsense2 as rs
import numpy as np
import os
import cv2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict

from Server.Location import RobotLocation
from Server.Vision.Court import Court
from Server.Vision.Birdie import Birdie
"""
This class is used to track:
    - the robot position (aruco marker)
    - the court position (all relevant points) (aruco marker)
    - the birdie positions (timestep, id, x, y, z)

This class exposes the information of the objects.
"""
class RealsenseServer:

    def __init__(self, robotArucoId, courtArucoId, minAreaThreshold = 500, maxAreaThreshold = 8000):
        # ================
        # Data
        # ================
        # State
        # CalibrationMatrix = np.zeros((4, 4))
        # self.MarkerCentroids = np.zeros((250, 3))
        # self.MarkerAges = np.full(250, -1)
        # self.CurrentTime = 0
        self.robotArucoId = robotArucoId
        self.courtArucoId = courtArucoId
        self.minAreaThreshold = minAreaThreshold
        self.maxAreaThreshold = maxAreaThreshold
        self.robotArucoVisible = None
        self.courtArucoVisible = None
        self.courtArucoHasBeenFound = False
        self.robot: RobotLocation = None
        self.tracked_hitbirdie = None
        self.court: Court = Court()
        self.contour_history = []

        # Config
        self.LIFETIME_THRESHOLD = 3
        self.BackgroundFilePath = "BackgroundImage.png"
        self.court_pos_file_path = "court_position.json"

        # ================
        # Realsense Setup
        # ================
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.depth_intrinsics = None

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        device_product_line = str(device.get_info(rs.camera_info.product_line))

        foundRGBCamera = False
        for s in device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                foundRGBCamera = True
                break
        if not foundRGBCamera:
            print("The demo requires Depth camera with Color sensor")
            exit(0)

        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

        # ArUco
        arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        arucoParams = cv2.aruco.DetectorParameters()
        self.arucoDetector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)

        # Start streaming
        self.pipeline.start(self.config)

        ### get the background frame:
        for i in range(16):
            self.pipeline.wait_for_frames()

        if os.path.exists(self.BackgroundFilePath):
            self.background = cv2.imread(self.BackgroundFilePath)
            self.background = cv2.cvtColor(self.background, cv2.COLOR_BGR2GRAY)
        else:
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            background = np.asanyarray(color_frame.get_data())
            self.background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(self.BackgroundFilePath, self.background)

        ### get the court coordinates from json file
        if os.path.exists(self.court_pos_file_path):
            print("court object loaded from json file")
            with open(self.court_pos_file_path, "r") as file:
                loaded_data = json.load(file)
                self.court_z = loaded_data.pop("Z")
                court_corners = [corner for corner in loaded_data.values()]
                self.court.set_corners(court_corners=court_corners)

    # This function captures a frame
    def capture_frame(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        self.depth_intrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
        if not depth_frame or not color_frame:
            return
        color_image = np.asanyarray(color_frame.get_data())
        return depth_frame, color_image

    # This function captures the second background frame after a birdie hit
    def capture_hit_background(self):
        _, background = self.capture_frame()
        self.hit_background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)

    # This function detects aruco markers (court and robot)
    def detect_arucos(self, image=None):
        if image is not None:
            depth_frame, color_image = image
        else:
            depth_frame, color_image = self.capture_frame()
        # Detect aruco markers
        aruco_corners, aruco_ids, rejected = self.arucoDetector.detectMarkers(color_image)

        # Set the current visibility status for both of the arucos
        if aruco_ids is not None and len(aruco_ids) > 0:
            if any(aruco_id[0] == self.courtArucoId for aruco_id in aruco_ids):
                self.courtArucoVisible = True
                self.courtArucoHasBeenFound = True
            else:
                self.courtArucoVisible = False
            if any(aruco_id[0] == self.robotArucoId for aruco_id in aruco_ids):
                self.robotArucoVisible = True
            else:
                self.robotArucoVisible = False
        else:
            self.courtArucoVisible = False
            self.robotArucoVisible = False

        for i, cornerSet in enumerate(aruco_corners):
            assert(cornerSet.shape[0] == 1)
            cornerSet = cornerSet[0, ...]

            (cornerA_x, cornerA_y) = cornerSet[0]
            (cornerB_x, cornerB_y) = cornerSet[2]

            centerSS = [(cornerA_x + cornerB_x) / 2.0, (cornerA_y + cornerB_y) / 2]
            centerZ = depth_frame.get_distance(centerSS[0], centerSS[1])

            centerRS = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, centerSS, centerZ)
            centerRS = [centerSS[0], centerSS[1], centerZ]

            id = aruco_ids[i][0]

            if centerZ != 0:
                # Match the aruco marker to the robot or the court
                if id == self.robotArucoId:
                    bottom_left = cornerSet[3]
                    top_left = cornerSet[0]
                    bottom_left = cornerSet[3]
                    theta = self.aruco_angle(top_left, bottom_left) # TODO Validate if this is the correct angle
                    if self.robot is None:
                        self.robot = RobotLocation(*centerRS, theta)
                    else:
                        self.robot.update(*centerRS, theta)
                elif id == self.courtArucoId:
                    if not self.court.is_locked:
                        if centerZ == 0:
                            raise Exception("Depth value for Court Aruco == 0 => Place court further towards the center of the boundary")
                        self.court_z = centerZ

                        self.court.set_corners(aruco_corners = cornerSet)
                else:
                    print("Unidentified aruco marker at: ", centerRS)

    # This function checks, if both aruco markers (robot, court) are detected
    def found_arucos(self):
        return self.robot is not None and self.court is not None

    def contours_are_static(self):
        current_contours = sorted(self.contour_history[-1])
        if len(self.contour_history) > 10:
            prev_contours = sorted(self.contour_history[-10])
            return len(current_contours) == len(prev_contours) and np.allclose(current_contours, prev_contours, atol=0.005, rtol=0)
        else:
            return False


    # This function detects aruco markers and birdies and store stheir positions
    def detect_birdies(self, visualize=True):
        # # Initialize the backround after a short delay
        # if cv2.waitKey(1) & 0xFF == ord('r'):
        #     print("reset at frame", self.CurrentTime)
        #     # Reset background
        #     self.capture_hit_background()

        # ==== FRAME QUERYING ====
        depth_frame, color_image = self.capture_frame()


        # ==== MARKER TRACKING ====
        aruco_corners, aruco_ids, rejected = self.arucoDetector.detectMarkers(color_image)

        # ==== BIRDIE TRACKING ====
        ### information ###
        # x is the width value. Center of camera is 0 width right going positiv
        # y is the height value. Center of camera is 0 width downwards going positiv
        # z is the deph value starting at 0 with increasing value with higher distance
        ### information ###
        # Convert current frame to grayscale
        gray_frame = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Subtract background
        diff = cv2.absdiff(self.hit_background, gray_frame)

        # Threshold to create a binary mask
        _, mask = cv2.threshold(diff, 45, 255, cv2.THRESH_BINARY)
        #threshhold, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Apply morphological operations to clean the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Apply morphological closing to merge nearby contours
        # This kernelsize was chosen to merge the head and the feathers of the birdie into one object
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel2)

        viable_contours = []

        # Find contours of the birdies
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            contourArea = cv2.contourArea(contour)
            if contourArea > self.minAreaThreshold and contourArea < self.maxAreaThreshold:  # Filter small blobs

                x, y, w, h = cv2.boundingRect(contour)
                centerSS = (int(x + w/2), int(y + h/2))
                centerZ = depth_frame.get_distance(centerSS[0], centerSS[1])
                centerRS = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, centerSS, centerZ)
                # TODO CHECK
                centerRS = [centerSS[0], centerSS[1], centerZ]
                viable_contours.append(centerRS)

                if self.tracked_hitbirdie:
                    # Update existing birdie
                    self.tracked_hitbirdie.update(*centerRS, (x,y,w,h), contour, self.court_z)
                else:
                    print("Create a new Birdie")
                    # Create new birdie
                    self.tracked_hitbirdie = Birdie(*centerRS, False, (x, y, w, h), contour)

        self.contour_history.append(viable_contours)

        # ==== Visualize ==== #
        if visualize:

            # Drawing params
            fontScale = 2.3
            fontFace = cv2.FONT_HERSHEY_PLAIN
            fontColor = (0, 255, 0)
            fontThickness = 2
            length = 50

            birdie = self.tracked_hitbirdie
            if birdie:
                x, y, w, h = birdie.bounding_rect
                bx, by, bz = int(birdie.x), int(birdie.y), int(birdie.z)
                # cv2.putText(color_image, f"ID: {birdie.id}",(x, y - 10), fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
                # TODO Before (birdie.x, birdie.y) was CenterSS !!Validate if it works)
                cv2.putText(color_image, str(round(bz, 2)), (bx, by), fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
                cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if birdie.impact_position:
                    ip = birdie.impact_position
                    cv2.rectangle(color_image, (ip.x - 3, ip.y -3), (ip.x + 3, ip.y + 3),  (0, 255, 0), 2)

            # TODO Validate result

            #end_x = int(bx + length * np.cos(np.radians(birdie.angle)))
            #end_y = int(by+ length * np.sin(np.radians(birdie.angle)))
            #cv2.line(color_image, (bx, by), (end_x, end_y), (255, 0, 0), 2)
            #if self.CurrentTime % 20 == 0:
                #print("Birdie", birdie.id, bx, birdie.x, by, birdie.y)
                #print(x,y)


        ### BADMINTON COURT VISUALIZATION
        if self.court:
            #court_corners = [self.court.CL, self.court.CR, self.court.STL, self.court.STM, self.court.STR, self.court.SBR, self.court.SBM, self.court.SBL]
            #labels = ['CL', 'CR', 'STL', 'STM', 'STR', 'SBR', 'SBM', 'SBL']

            # Define connections for the court and serving box
            court_connections = [(self.court.CL, self.court.CR)]  # Only one line for court boundary
            serve_box_connections = [
                (self.court.STL, self.court.STM),  # Top of the serving box
                (self.court.STM, self.court.STR),
                (self.court.STR, self.court.SBR),  # Right side
                (self.court.SBR, self.court.SBM),  # Bottom of the serving box
                (self.court.SBM, self.court.SBL),
                (self.court.SBL, self.court.STL),  # Left side
                (self.court.SBM, self.court.STM)
            ]

            # Draw court boundary lines
            for corner1, corner2 in court_connections:
                cv2.line(color_image,
                        (int(corner1.x), int(corner1.y)),
                        (int(corner2.x), int(corner2.y)),
                        (255, 0, 0), 2)  # Blue for court boundary

            # Draw serving box lines
            for corner1, corner2 in serve_box_connections:
                cv2.line(color_image,
                        (int(corner1.x), int(corner1.y)),
                        (int(corner2.x), int(corner2.y)),
                        (0, 0, 255), 2)  # Red for serving box

            # Annotate the corners
            labels = ['CL', 'CR', 'STL', 'STM', 'STR', 'SBR', 'SBM', 'SBL']
            court_corners = [self.court.CL, self.court.CR, self.court.STL, self.court.STM, self.court.STR, self.court.SBR, self.court.SBM, self.court.SBL]
            for i, corner in enumerate(court_corners):
                cv2.circle(color_image, center=(int(corner.x), int(corner.y)), radius=5, color=(0, 255, 0), thickness=-1)
                cv2.putText(color_image, labels[i], (int(corner.x) + 10, int(corner.y) + 10), fontFace, (fontScale * 0.4), (0, 255, 0), fontThickness, cv2.LINE_AA)


        ### ARUCO MARKER VISUALIZATION ###
        # Draw aruco markers for robot and field court
        color_image = cv2.aruco.drawDetectedMarkers(color_image,aruco_corners,aruco_ids)
        depth_image = np.asanyarray(depth_frame.get_data())
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        depth_colormap_dim = depth_colormap.shape
        color_colormap_dim = color_image.shape

        # If depth and color resolutions are different, resize color image to match depth image for display
        if depth_colormap_dim != color_colormap_dim:
            resized_color_image = cv2.resize(color_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
            images = np.hstack((resized_color_image, depth_colormap))
        else:
            images = np.hstack((color_image, depth_colormap))



        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        cv2.imshow("Mask", mask)
        cv2.waitKey(1)

        # ==== DEBUG END ====

        # self.CurrentTime += 1

    # This function detects birdies at collection time
    def detect_collection_birdies(self, visualize = False):
        # ==== FRAME QUERYING ====
        depth_frame, color_image = self.capture_frame()

        ### --- Birdie Tracking Code --- ###
        ### information ###
        # x is the width value. Center of camera is 0 width right going positiv
        # y is the height value. Center of camera is 0 width downwards going positiv
        ### information ###
        # Convert current frame to grayscale
        gray_frame = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # Subtract background
        diff = cv2.absdiff(self.background, gray_frame)

        # Threshold to create a binary mask
        _, mask = cv2.threshold(diff, 100, 255, cv2.THRESH_BINARY)
        #threshhold, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        #print(threshhold)
        # Apply morphological operations to clean the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Apply morphological closing to merge nearby contours
        # This kernelsize was chosen to merge the head and the feathers of the birdie into one object
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel2)

        # Find contours of the birdies
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        birdiesList = []
        for contour in contours:
            contourArea = cv2.contourArea(contour)
            if contourArea > self.minAreaThreshold and contourArea < self.maxAreaThreshold:  # Filter small blobs
                print(f"Birdie, CA: {contourArea}")

                x, y, w, h = cv2.boundingRect(contour)
                centerSS = (int(x + w/2), int(y + h/2))
                centerZ = depth_frame.get_distance(centerSS[0], centerSS[1])
                centerRS = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, centerSS, centerZ)
                centerRS = [centerSS[0], centerSS[1], centerZ]

                newBirdie = Birdie(*centerRS, False, (x, y, w, h), contour)
                birdiesList.append(newBirdie)

        # ==== Visualize ==== #
        if visualize:

            # Drawing params
            fontScale = 2.3
            fontFace = cv2.FONT_HERSHEY_PLAIN
            fontColor = (0, 255, 0)
            fontThickness = 2
            length = 50

            for birdie in birdiesList:
                x, y, w, h = birdie.bounding_rect
                bx, by, bz = int(birdie.x), int(birdie.y), int(birdie.z)
                # cv2.putText(color_image, f"ID: {birdie.id}",(x, y - 10), fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
                # TODO Before (birdie.x, birdie.y) was CenterSS !!Validate if it works)
                cv2.putText(color_image, str(round(bz, 2)), (bx, by), fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
                cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # TODO Validate result

                #end_x = int(bx + length * np.cos(np.radians(birdie.angle)))
                #end_y = int(by+ length * np.sin(np.radians(birdie.angle)))
                #cv2.line(color_image, (bx, by), (end_x, end_y), (255, 0, 0), 2)
                #if self.CurrentTime % 20 == 0:
                    #print("Birdie", birdie.id, bx, birdie.x, by, birdie.y)
                    #print(x,y)

            cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense', color_image)
            cv2.imshow('Mask', mask)
            cv2.waitKey(1)

        return birdiesList

    def save_court_position(self):
        print("save_court_position_called")
        if os.path.exists(self.court_pos_file_path):
            return

        while not self.court.is_locked:
            depth_frame, color_image = self.capture_frame()
            self.detect_arucos(image=[depth_frame, color_image]) # This updates the court object
            if self.courtArucoHasBeenFound == False:
                continue

            # Define connections for the court and serving box
            court_connections = [(self.court.CL, self.court.CR)]  # Only one line for court boundary
            serve_box_connections = [
                (self.court.STL, self.court.STM),  # Top of the serving box
                (self.court.STM, self.court.STR),
                (self.court.STR, self.court.SBR),  # Right side
                (self.court.SBR, self.court.SBM),  # Bottom of the serving box
                (self.court.SBM, self.court.SBL),
                (self.court.SBL, self.court.STL),  # Left side
                (self.court.SBM, self.court.STM)
            ]

            # Draw court boundary lines
            for corner1, corner2 in court_connections:
                cv2.line(color_image,
                        (int(corner1.x), int(corner1.y)),
                        (int(corner2.x), int(corner2.y)),
                        (255, 0, 0), 2)  # Blue for court boundary

            # Draw serving box lines
            for corner1, corner2 in serve_box_connections:
                cv2.line(color_image,
                        (int(corner1.x), int(corner1.y)),
                        (int(corner2.x), int(corner2.y)),
                        (0, 0, 255), 2)  # Red for serving box

            # Annotate the corners
            labels = ['CL', 'CR', 'STL', 'STM', 'STR', 'SBR', 'SBM', 'SBL']
            court_corners = [self.court.CL, self.court.CR, self.court.STL, self.court.STM, self.court.STR, self.court.SBR, self.court.SBM, self.court.SBL]
            print(self.court.SBL)
            fontScale = 2.3
            fontFace = cv2.FONT_HERSHEY_PLAIN
            fontThickness = 2
            for i, corner in enumerate(court_corners):
                cv2.circle(color_image, center=(int(corner.x), int(corner.y)), radius=5, color=(0, 255, 0), thickness=-1)
                cv2.putText(color_image, labels[i], (int(corner.x) + 10, int(corner.y) + 10), fontFace, (fontScale * 0.4), (0, 255, 0), fontThickness, cv2.LINE_AA)

            cv2.namedWindow('CourtOrienting', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('CourtOrienting', color_image)

            # Wait till keypress which will initiate saving court position into file
            if cv2.waitKey(1) & 0xFF == ord('r'):
                self.court.is_locked = True
                cv2.destroyAllWindows()

        # order must match initialization order in CourtLocation class
        data = {
            "Z": self.court_z,
            "CL": self.court.CL.get_pos(),
            "CR": self.court.CR.get_pos(),
            "STL": self.court.STL.get_pos(),
            "STM": self.court.STM.get_pos(),
            "STR": self.court.STR.get_pos(),
            "SBR": self.court.SBR.get_pos(),
            "SBM": self.court.SBM.get_pos(),
            "SBL": self.court.SBL.get_pos(),
        }
        print(data)
        with open(self.court_pos_file_path, "w") as file:
            json.dump(data, file)

        return




    # --- Helper Methods --- #
    # Find theta angle (angle on y-axis between top left and bottom left corner)
    def aruco_angle(self, corner_top_left, corner_bottom_left):
        delta_x = (corner_bottom_left[0] - corner_top_left[0])
        delta_y = (corner_bottom_left[1] - corner_top_left[1])
        theta = np.arctan2(delta_y, delta_x)

        return theta

    def prepare_birdie_tracking(self):
        self.tracked_hitbirdie = None
        self.contour_history = []