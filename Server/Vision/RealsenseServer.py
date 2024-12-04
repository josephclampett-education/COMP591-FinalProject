import select
import json
import pyrealsense2 as rs
import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Server.Vision.Court import Court
from Server.Location import RobotLocation, BirdieLocation
from typing import List
"""
This class is used to track:
    - the robot position (aruco marker)
    - the court position (all relevant points) (aruco marker)
    - the birdie positions (timestep, id, x, y, z)

This class exposes the information of the objects.
"""
class RealsenseServer:

    def __init__(self, robotArucoId, courtArucoId):
        # ================
        # Data
        # ================
        # Sequence
        self.DEBUG = False
        self.DEBUG = True

        # State
        # CalibrationMatrix = np.zeros((4, 4))
        self.MarkerCentroids = np.zeros((250, 3))
        self.MarkerAges = np.full(250, -1)
        self.CurrentTime = 0
        self.robotArucoId = robotArucoId
        self.courtArucoId = courtArucoId
        self.robot: RobotLocation
        self.birdies: List[BirdieLocation] = []
        self.court: Court

        # Config
        self.LIFETIME_THRESHOLD = 3

        # ================
        # Realsense Setup
        # ================
        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()

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

        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # ArUco
        arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        arucoParams = cv2.aruco.DetectorParameters()
        self.arucoDetector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)

        # Start streaming
        self.pipeline.start(self.config)

        ### get the background frame:
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        background = np.asanyarray(color_frame.get_data())
        self.background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)

        # TODO: Test this code!#################################
        # Retrieve camera intrinsics
        color_intrinsics = color_frame.profile.as_video_stream_profile().intrinsics
        self.camera_matrix = np.array([[color_intrinsics.fx, 0, color_intrinsics.ppx],
                                       [0, color_intrinsics.fy, color_intrinsics.ppy],
                                       [0, 0, 1]])
        self.dist_coeffs = np.array([color_intrinsics.coeffs])
        #########################################################

        ### Store the birdie positions
        self.birdie_positions = pd.DataFrame(columns=['frame', 'id', 'x', 'y', 'z'])

    # Find theta angle (angle on y-axis between top left and bottom left corner)
    def aruco_angle(self, corner_top_left, corner_bottom_left):
        delta_x = (corner_bottom_left[0] - corner_top_left[0])
        delta_y = (corner_bottom_left[1] - corner_top_left[1])
        theta = np.arctan2(delta_y, delta_x)
        return theta


    # This function detects aruco markers and birdies and store stheir positions
    def detect(self):
        # ==== FRAME QUERYING ====
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            return
        color_image = np.asanyarray(color_frame.get_data())

        # ==== MARKER TRACKING ====
        corners, ids, rejected = self.arucoDetector.detectMarkers(color_image)
        depthIntrinsics = depth_frame.profile.as_video_stream_profile().intrinsics

        for i, cornerSet in enumerate(corners):
            assert(cornerSet.shape[0] == 1)
            cornerSet = cornerSet[0, ...]

            (cornerA_x, cornerA_y) = cornerSet[0]
            (cornerB_x, cornerB_y) = cornerSet[2]

            centerSS = [(cornerA_x + cornerB_x) / 2.0, (cornerA_y + cornerB_y) / 2]
            centerZ = depth_frame.get_distance(centerSS[0], centerSS[1])

            centerRS = rs.rs2_deproject_pixel_to_point(depthIntrinsics, centerSS, centerZ)

            id = ids[i][0]
            self.MarkerCentroids[id] = centerRS
            if self.MarkerAges[id] != -2:
                self.MarkerAges[id] = self.CurrentTime
            
            if id == self.robotArucoId:
                print("Robot position: ", centerRS)
                bottom_left = cornerSet[3]
                top_left = cornerSet[0]
                bottom_left = cornerSet[3]
                theta = self.aruco_angle(top_left, bottom_left)
                self.robot = RobotLocation.__init__(*centerRS, theta)
            elif id == self.courtArucoId:
                print("Court position: ", centerRS)
                self.court = Court.__init__(cornerSet)
            else:
                print("Unidentified aruco marker at: ", centerRS)
            
            #theta, delta_x, delta_y = self.aruco_angle(cornerSet[0], cornerSet[1])
            #if self.CurrentTime % 100 == 0:
            #    print("theta", np.rad2deg(theta))
            #    print("xdelta", delta_x)
            #    print("ydelta", delta_y)

        # ==== Process all incoming markers ====
        outLiveMarkerIds = []
        outLiveMarkerPositionsRS = []
        for i, markerAge in enumerate(self.MarkerAges):
            # Ignore calibrants and unencountereds
            if markerAge < 0:
                continue

            outId = i
            outCentroidRS = [-999.0, -999.0, -999.0]
            if (self.CurrentTime - markerAge) > self.LIFETIME_THRESHOLD:
                outCentroidRS = [-999.0, -999.0, -999.0 ]
            else:
                centroid = self.MarkerCentroids[i]
                centroid = np.append(centroid, 1.0)
                outCentroidRS = [centroid[0].item(), centroid[1].item(), centroid[2].item()]

            outLiveMarkerIds.append(outId)
            outLiveMarkerPositionsRS.append(outCentroidRS)



        # ==== DEBUG START ====
        if self.DEBUG:
            color_image = cv2.aruco.drawDetectedMarkers(color_image,corners,ids)
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

            ### Birdie Tracking Code ###
            ### information ###
            # x is the width value. Center of camera is 0 width right going positiv
            # y is the height value. Center of camera is 0 width downwards going positiv
            # z is the deph value starting at 0 with increasing value with higher distance
            ### information ###
            # Convert current frame to grayscale
            gray_frame = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

            # Subtract background
            diff = cv2.absdiff(self.background, gray_frame)

            # Threshold to create a binary mask
            _, mask = cv2.threshold(diff, 45, 255, cv2.THRESH_BINARY)
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
            id_counter = 0
            for contour in contours:
                if cv2.contourArea(contour) > 50:  # Filter small blobs
                    # Asign an id to the contour object
                    birdie_id = id_counter
                    id_counter += 1

                    x, y, w, h = cv2.boundingRect(contour)
                    centerSS = (int(x + w/2), int(y + h/2))
                    centerZ = depth_frame.get_distance(centerSS[0], centerSS[1])
                    centerRS = rs.rs2_deproject_pixel_to_point(depthIntrinsics, centerSS, centerZ)

                    # Append to DataFrame
                    new_row = pd.DataFrame([{
                        'frame': self.CurrentTime,
                        'id': birdie_id,
                        'x': centerRS[0],
                        'y': centerRS[1],
                        'z': centerZ
                    }])

                    # Use pd.concat() to add the new row to the DataFrame
                    self.birdie_positions = pd.concat([self.birdie_positions, new_row], ignore_index=True)


                    fontScale = 2.3
                    fontFace = cv2.FONT_HERSHEY_PLAIN
                    fontColor = (0, 255, 0)
                    fontThickness = 2
                    cv2.putText(color_image, f"ID: {birdie_id}", (x, y - 10), fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
                    cv2.putText(color_image, str(round(centerZ, 2)), centerSS, fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
                    cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            """
            if self.CurrentTime == 200:
                print("200 timestep")
                # Filter for unique birdie IDs

            # Create a 3D plot

                # Filter the DataFrame for a specific birdie ID if desired (optional)
                birdie_id_to_plot = 0  # Change this to the birdie ID you want to plot
                birdie_data = self.birdie_positions[self.birdie_positions['id'] == birdie_id_to_plot]
                #print(birdie_data)
                # Extract the coordinates
                x = birdie_data['x']
                y = birdie_data['y']
                z = birdie_data['z']
                frame = birdie_data['frame']  # Optional for color

                # Create the 3D plot
                fig = plt.figure(figsize=(10, 7))
                ax = fig.add_subplot(111, projection='3d')

                # Scatter plot (3D)
                sc = ax.scatter(x, z, -y, c=frame, cmap='viridis', label=f'Birdie {birdie_id_to_plot}')
                plt.colorbar(sc, label='Frame')

                # Optional: Connect points with a line
                ax.plot(x, z, -y, color='gray', alpha=0.5)

                # Labels and title
                ax.set_title(f"3D Trajectory of Birdie {birdie_id_to_plot}")
                ax.set_xlabel('X Position')
                ax.set_ylabel('Y Position(RS: Z)')
                ax.set_zlabel('Z Position(RS: -y)')
                ax.legend()

                ax.set_xlim(-2, 2)  # Replace with your desired range for x-axis
                ax.set_ylim(0, 5)  # Replace with your desired range for y-axis
                ax.set_zlim(-2, 2)  # Replace with your desired range for z-axis

                # Show plot
                plt.show()

                # Add labels, legend, and title
                ax.set_title("3D Trajectories of All Birdies")
                ax.set_xlabel('X Position')
                ax.set_ylabel('Y Position')
                ax.set_zlabel('Z Position')
                ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.05))

                # Show plot
                plt.show()
                """
            """
            # Display results
            cv2.imshow("Background Subtraction", color_image)
            cv2.imshow("Mask", mask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("amount of datapoints", self.birdie_positions.shape)
                print("timestep: ", self.CurrentTime)
                break
            elif cv2.waitKey(1) & 0xFF == ord('r'):
                print("reset at frame", self.CurrentTime)
                # Reset background
                frames = pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                background = np.asanyarray(color_frame.get_data())
                background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)

                # Reset time and dataframe
                self.CurrentTime = 0
                self.birdie_positions = self.birdie_positions.drop(self.birdie_positions.index)

                """
        
        ### Court border tracking code ###
        colors = [(0, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0)]
        """
        for i in range(court_corners_RS.shape[0]):
                court_corner = court_corners_RS[i]
                print(court_corners_RS)
                print("test", court_corner)
                cv2.circle(images, center=(int(court_corner[0]), int(court_corner[1])), radius=2, color=colors[i], thickness=2)
                
                fontScale = 2.3
                fontFace = cv2.FONT_HERSHEY_PLAIN
                fontColor = (0, 255, 0)
                fontThickness = 2
                cv2.putText(images, f"ID: 10", (0, 0), fontFace, fontScale, fontColor, fontThickness, cv2.LINE_AA)
       
            # Show images
        """
        
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        cv2.waitKey(1)

        # ==== DEBUG END ====

        self.CurrentTime += 1