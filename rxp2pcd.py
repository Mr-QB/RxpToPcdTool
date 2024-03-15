import ctypes
import sys
from ctypes import *
import open3d as o3d
import numpy as np

# Define basic types
int8 = c_int8
uint8 = c_uint8
int16 = c_int16
uint16 = c_uint16
int32 = c_int32
uint32 = c_uint32
int64 = c_int64
uint64 = c_uint64
float32 = c_float
float64 = c_double

# Define library I/O types
TLibResult = int32
TLibHandle = c_void_p
TLibString = c_char_p


# Define point record types
class TRecordXYZ(Structure):
    _fields_ = [("x", float32), ("y", float32), ("z", float32)]


class TRecordMisc(Structure):
    _fields_ = [
        ("amplitude", float32),
        ("reflectance", float32),
        ("deviation", uint16),
        ("flags", uint16),
        ("background_radiation", float32),
    ]


class TRecordTime(Structure):
    _fields_ = [("time", uint64)]


# Load library
lib = CDLL("lib\scanifc-mt-s.dll")

# Get library function prototypes
lib.scanifc_get_library_version.restype = TLibResult
lib.scanifc_get_last_error.restype = TLibResult
lib.scanifc_point3dstream_open.restype = TLibResult
lib.scanifc_point3dstream_read.restype = TLibResult
lib.scanifc_point3dstream_close.restype = TLibResult

# Get library version
major = uint16()
minor = uint16()
build = uint16()
lib.scanifc_get_library_version(byref(major), byref(minor), byref(build))
print("Library version: {}.{}.{}".format(major.value, minor.value, build.value))

# Open RXP file (or stream)
handle = TLibHandle()
uri = c_char_p(b"file:scan.rxp")
sync_to_pps = int32(0)
lib.scanifc_point3dstream_open(uri, sync_to_pps, byref(handle))

BLOCK_SIZE = 1024  # The number of point cloud points per reading
bufferXYZ = (TRecordXYZ * BLOCK_SIZE)()
bufferMISC = (TRecordMisc * BLOCK_SIZE)()
bufferTIME = (TRecordTime * BLOCK_SIZE)()
point_cloud = o3d.geometry.PointCloud()  # Initialize the point cloud
# Read points from stream
point_cloud_array = []
frames = 0
time = 0
while True:
    got = uint32()
    end_of_frame = int32()

    lib.scanifc_point3dstream_read(
        handle,  # Handle to the data stream
        BLOCK_SIZE,  # Number of points to read per call
        byref(bufferXYZ),  # Buffer for XYZ coordinates of the points
        byref(bufferMISC),  # Buffer for miscellaneous attributes of the points
        byref(bufferTIME),  # Buffer for timestamps of the points
        byref(got),  # Variable to store the number of points read
        byref(end_of_frame),  # Variable to indicate the end of a frame
    )
    if end_of_frame.value == 1:
        frames += 1
    if got.value == 0:
        break
    for i in range(got.value):
        xyz = bufferXYZ[i]
        # misc = bufferMISC[i]
        time = bufferTIME[i].time * 1e-9
        point_cloud_array.append([xyz.x, xyz.y, xyz.z])
    # print("{:.3f};{:.3f};{:.3f};{:.6f};{:.2f};{:.2f};{}".format(
    #     xyz.x, xyz.y, xyz.z, time, misc.amplitude, misc.reflectance, misc.deviation))
point_cloud.points = o3d.utility.Vector3dVector(np.array(point_cloud_array))
o3d.io.write_point_cloud("outputs.pcd", point_cloud)  # Write pcd-file
# Close stream
lib.scanifc_point3dstream_close(handle)
