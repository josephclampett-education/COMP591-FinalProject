import select
import json
import pyrealsense2 as rs
import numpy as np
import cv2

# ================
# Data
# ================
# Sequence
DEBUG = False
DEBUG = True

# State
# CalibrationMatrix = np.zeros((4, 4))
MarkerCentroids = np.zeros((250, 3))
MarkerAges = np.full(250, -1)
CurrentTime = 0

# Config
LIFETIME_THRESHOLD = 3

# ================
# Realsense Setup
# ================
# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
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

config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

# ArUco
arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
arucoParams = cv2.aruco.DetectorParameters()
arucoDetector = cv2.aruco.ArucoDetector(arucoDict, arucoParams)

# Start streaming
pipeline.start(config)

# ================
# Server loop
# ================
while True:
	# ==== FRAME QUERYING ====
	frames = pipeline.wait_for_frames()
	depth_frame = frames.get_depth_frame()
	color_frame = frames.get_color_frame()
	if not depth_frame or not color_frame:
		continue
	color_image = np.asanyarray(color_frame.get_data())

	# ==== MARKER TRACKING ====
	corners, ids, rejected = arucoDetector.detectMarkers(color_image)
	depthIntrinsics = depth_frame.profile.as_video_stream_profile().intrinsics
	
	for i, cornerSet in enumerate(corners):
		assert(cornerSet.shape[0] == 1)
		cornerSet = cornerSet[0, ...]

		(cornerA_x, cornerA_y) = cornerSet[0]
		(cornerB_x, cornerB_y) = cornerSet[2]

		centerSS = [(cornerA_x + cornerB_x) / 2.0, (cornerA_y + cornerB_y) / 2]
		centerZ = depth_frame.get_distance(centerSS[0], centerSS[1])

		centerWS = rs.rs2_deproject_pixel_to_point(depthIntrinsics, centerSS, centerZ)
		
		id = ids[i][0]
		MarkerCentroids[id] = centerWS
		if MarkerAges[id] != -2:
			MarkerAges[id] = CurrentTime
			
	# ==== Process all incoming markers ==== 
	outLiveMarkerIds = []
	outLiveMarkerPositionsRS = []
	for i, markerAge in enumerate(MarkerAges):
		# Ignore calibrants and unencountereds
		if markerAge < 0:
			continue

		outId = i
		outCentroidRS = {"x": -999.0, "y": -999.0, "z": -999.0}
		if (CurrentTime - markerAge) > LIFETIME_THRESHOLD:
			outCentroidRS = {"x": -999.0, "y": -999.0, "z": -999.0}
		else:
			centroid = MarkerCentroids[i]
			centroid = np.append(centroid, 1.0)
			outCentroidRS = {"x": centroid[0].item(), "y": centroid[1].item(), "z": centroid[2].item()}
		
		outLiveMarkerIds.append(outId)
		outLiveMarkerPositionsRS.append(outCentroidRS)

	# Show images
	cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
	cv2.imshow('RealSense', color_image)
	cv2.waitKey(1)

	CurrentTime += 1