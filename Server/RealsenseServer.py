import socket
import select
import json
import pyrealsense2 as rs
import numpy as np
import cv2

# ================
# Pre-init
# ================
class RoundingFloat(float):
	__repr__ = staticmethod(lambda x: format(x, '.5f'))

json.encoder.c_make_encoder = None
json.encoder.float = RoundingFloat

# ================
# Data
# ================
# Server
HOST = "127.0.0.1" # The server's hostname or IP address
PORT = 80          # The port used by the server

# Sequence
HasCalibrated = False
DEBUG = False
DEBUG = True

# State
CalibrationMatrix = np.zeros((4, 4))
MarkerCentroids = np.zeros((250, 3))
MarkerAges = np.full(250, -1)
CurrentTime = 0

# Config
LIFETIME_THRESHOLD = 3

# ================
# Networking Utils
# ================
def receive(sock):
	data = sock.recv(4*1024)
	data = data.decode('utf-8')
	msg = json.loads(data)
	print("Received: ", msg)
	return msg

def send(sock, msg):
	data = json.dumps(msg)
	sock.sendall(data.encode('utf-8'))
	print("Sent: ", msg)

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
try:
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect((HOST, PORT))
		sock.setblocking(0)

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

			# ==== SERVER MESSAGES ====
			if HasCalibrated == False:
				try:
					msg = receive(sock)

					# Really shouldn't need this line
					if (len(msg) == 0):
						print("Zero-length message")
						continue

					calibrationIds = msg["CalibrationIds"]
					calibrationPositionsUS = msg["CalibrationPositionsUS"]

					calibrationCount = len(calibrationIds)

					calibrationPointsRS = np.zeros((calibrationCount, 4))
					calibrationPointsUS = np.zeros((calibrationCount, 4))
					for i, calibrationId in enumerate(calibrationIds):
						id = calibrationId
						posUS = calibrationPositionsUS[i]

						MarkerAges[id] = -2 # Lock the lifetime to indicate use in calibration

						calibrationPointsRS[i] = np.append(MarkerCentroids[id], 1.0)
						calibrationPointsUS[i] = [posUS['x'], posUS['y'], posUS['z'], 1.0]

					CalibrationMatrix, residuals, rank, s = np.linalg.lstsq(calibrationPointsRS, calibrationPointsUS, rcond = None)
					
					outMatrix = CalibrationMatrix.tolist()
					with open("CalibrationMatrix.json", 'w') as json_file:
						json.dump(outMatrix, json_file)

					HasCalibrated = True
				except:
					pass
			else:
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
				msg["LiveIds"] = outLiveMarkerIds
				msg["LivePositionsRS"] = outLiveMarkerPositionsRS

				# ==== Create basis info ==== 
				calibratedOrigin = CalibrationMatrix.transpose().dot([0, 0, 0, 1.0])
				msg["CalibratedOriginUS"] = {"x": calibratedOrigin[0].item(), "y": calibratedOrigin[1].item(), "z": calibratedOrigin[2].item()}
				calibratedForward = CalibrationMatrix.transpose().dot([0.0, 0, 1.0, 1.0])
				msg["CalibratedForwardUS"] = {"x": calibratedForward[0].item(), "y": calibratedForward[1].item(), "z": calibratedForward[2].item()}
				calibratedUp = CalibrationMatrix.transpose().dot([0.0, 1.0, 0, 1.0])
				msg["CalibratedUpUS"] = {"x": calibratedUp[0].item(), "y": calibratedUp[1].item(), "z": calibratedUp[2].item()}

				send(sock, msg)

				# Show images
				cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
				cv2.imshow('RealSense', color_image)
				cv2.waitKey(1)
			CurrentTime += 1
finally:
	# Stop streaming
	pipeline.stop()