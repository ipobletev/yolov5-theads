import os
import uuid
import fcntl
import socket
import struct
from dotenv import load_dotenv

# Get MAC 
def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return ':'.join('%02x' % b for b in info[18:24])

# Support uuid generator
gen_uuid = lambda txt: str(uuid.uuid3(type('', (), dict(bytes=b''))(), txt))

VOL_PATH = os.getenv('VOL_PATH', '../intemp')
load_dotenv(dotenv_path=VOL_PATH + "/.env")

#############################################
##### User configuration ####################
#############################################

# Version
DEVICE_NAME_MAC = os.getenv('DEVICE_NAME_MAC','eth0')
SCHEMA_VERSION = os.getenv('SCHEMA_VERSION', '1.0.0')
DEVICE_TYPE = os.getenv('DEVICE_TYPE', 'OVA')
DEVICE_ID = gen_uuid(str(getHwAddr(str(DEVICE_NAME_MAC))))
SENSOR_TYPE = os.getenv('SENSOR_TYPE', 'CAMERA')

#############################################
##### Platform ##############################
#############################################

#Path for modules
PYTHONPATH = os.getenv('PYTHONPATH', '')
if(PYTHONPATH==''):
    PYTHONPATH=os.getcwd() + '/modules'

#NVR distorsion
ENABLE_ANALYSIS_NVR_DISTORSION = (os.getenv('ENABLE_ANALYSIS_NVR_DISTORSION', 'False') == 'True')
NVR_DISTORSION = float(os.getenv('NVR_DISTORSION', '0.7'))

#disable program
DISABLE_OVA = (os.getenv('DISABLE_OVA', 'False') == 'True')

# Test
ENABLE_DEV = (os.getenv('ENABLE_DEV', 'False') == 'True')
ENABLE_LOG_FILE = (os.getenv('ENABLE_LOG_FILE', 'False') == 'True')

# Platform
VM_GUI = (os.getenv('VM_GUI', 'False') == 'True')

# Enable sends
ENABLE_SENDTO_CLOUD = (os.getenv('ENABLE_SENDTO_CLOUD', 'True') == 'True')
ENABLE_SENDTO_GPU = (os.getenv('ENABLE_SENDTO_GPU', 'True') == 'True')

# Reescale image
REESCALE_IMAGE_CLOUD = (0,0)
REESCALE_IMAGE_RAW_CLOUD  = (0,0)
REESCALE_IMAGE_GPU = (0,0)

# Attempt to recconect to camera
ATTEMPT_CAMERAS = 3

# Seconds ti send raw imagen to roi cloud.
TIME_SEND_ROIMAGE_TOCLOUD = int(os.getenv('TIME_SEND_DAILYIMAGE_TOCLOUD', '43200'))

# Out temp
PATH_OUTEMP=os.getenv('PATH_OUTEMP', 'temp')

# Time each time to processing each stream image
TIME_SECUENCE_TOPROCESING_IMAGEN = int(os.getenv('TIME_SECUENCE_TOPROCESING_IMAGEN', '5'))

#############################################
##### IDs ###################################
#############################################

STREAMSTXT_PATH = VOL_PATH + '/streams.txt'
    
STREAM_LIST = []

with open(STREAMSTXT_PATH, "r") as myfile:
   total_streams = sum(1 for line in myfile)

USE_DIRECT_UUID = (os.getenv('USE_DIRECT_UUID', 'False') == 'True')
with open(STREAMSTXT_PATH, "r") as myfile:   
    for i in range(total_streams):
        raw_text = myfile.readline()
        x = raw_text.split(",")

        if(USE_DIRECT_UUID==True):
            id_uuid = str(x[0])
        if(USE_DIRECT_UUID==False):
            id_uuid = gen_uuid(str(x[0]))

        STREAM_LIST.append({i : {}})
        STREAM_LIST[i] = {
            "id" : str(x[0]),
            "id_uuid" : id_uuid,
            "path" : str(x[1]),
            "threshold" : float(str(x[2])),
            "supp_threshold" : float(str(x[3]).rstrip('\r').rstrip('\n'))
        }