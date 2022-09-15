import json
from multiprocessing import Process, Queue
import userconfig
import torch
import os, glob,sys, fnmatch
from datetime import datetime, timezone
import uuid
import cv2
import time
from threading import Timer
from datetime import datetime, timezone
from utils.general import LOGGER
import threading
import modules.ImageProcessing

def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result[0]

def sendData_process(queue_data):

    #check queue
    while True:
        
        # Get frame uuid from queue
        if queue_data.qsize()>0:
            
            frame_uuid = queue_data.get()
            # Get json and image path
            json_relative_name = "temp_event_" + frame_uuid + "*"
            image_raw_relative_name = "temp_raw_" + frame_uuid + "*"
            image_wbb_relative_name = "temp_wbb_" + frame_uuid + "*"
            
            json_path = find(json_relative_name, 'temp/')
            image_raw_path = find(image_raw_relative_name, 'temp/')
            image_wbb_path = find(image_wbb_relative_name, 'temp/')
            
            # Load json
            with open(json_path) as json_file:
                json_content = json.load(json_file)
            
            timestamp = json_content["records"][0]["value"]["timestamp"]
            id_sensor= json_content["records"][0]["value"]["deviceId"]
            
            LOGGER.info("Data sent")
            #print(json_content)

            # # Send To Cloud GCP
            # #########################################

            # ### Send Image with bb
            # LOGGER.info("---------------------------------------------")
            # LOGGER.info("Envio de imagen bb a Cloud.")
            # cloud_name_image = str(uuid.uuid4())
            # device_id = userconfig.DEVICE_ID
            # status_cloudimage,cloud_imagename_url_bb = SendDataGCP.sendImageToCloud(image_wbb_path,
            #                                                     device_id,
            #                                                     id_sensor,
            #                                                     timestamp,
            #                                                     cloud_name_image,
            #                                                     cloudDir.EVALROI)
            # if status_cloudimage == 0:

            #     # Send Image without bb
            #     LOGGER.info("---------------------------------------------")
            #     LOGGER.info("Envio de imagen raw a Cloud.")
            #     device_id = userconfig.DEVICE_ID
            #     print(image_raw_path)
            #     status_rawimage, cloud_imagename_url_raw = SendDataGCP.sendImageRawImageToCloud(image_raw_path,
            #                                                         device_id,
            #                                                         id_sensor,
            #                                                         timestamp,
            #                                                         cloud_name_image,
            #                                                         cloudDir.MAIN)

            #     ### Send json
            #     LOGGER.info("---------------------------------------------")
            #     LOGGER.info("Envio de deteccion json a cloud.")
            #     SendDataGCP.publish_JsonToCloud(cloud_imagename_url_bb,json_path,credentials.TOKEN,
            #                                             cloudDir.EVALROI)

            # Delete temp image and jsondata
            os.remove(json_path)
            os.remove(image_raw_path)
            os.remove(image_wbb_path)
                
if __name__ == '__main__':
    
    # Clear terminal
    clear = lambda: os.system('clear')
    clear()

    # Delete temp image and jsondata
    for filename in glob.glob(userconfig.PATH_OUTEMP + "/temp_*"):
        os.remove(filename)
    
    LOGGER.info("#############################################")
    LOGGER.info("Inicializa sistema")
    LOGGER.info("#############################################")
    LOGGER.info("OpenCV version: "+ str(cv2.__version__))
    LOGGER.info("Python version: " + str(sys.version))
    LOGGER.info("Pytorch version: " + str(torch.__version__))
    LOGGER.info("Pytorch GPU count: " + str(torch.cuda.device_count()))
    LOGGER.info("Pytorch Cuda Available: " + str(torch.cuda.is_available()))
    LOGGER.info("---------------------------------------------")
    LOGGER.info("OVA Disable: " + str(userconfig.DISABLE_OVA))
    LOGGER.info("Save log file: " + str(userconfig.ENABLE_LOG_FILE))
    LOGGER.info("Send to cloud: " + str(userconfig.ENABLE_SENDTO_CLOUD))
    LOGGER.info("NVR Distorsion: " + str(userconfig.ENABLE_ANALYSIS_NVR_DISTORSION))
    LOGGER.info("Send to product: " + str(not(userconfig.SEND_TO_DEVELOP_CLOUD)))
    LOGGER.info("---------------------------------------------")
    LOGGER.info("Device: " + str(userconfig.DEVICE_TYPE))
    LOGGER.info("Device ID: " + str(userconfig.DEVICE_ID))
    LOGGER.info("Sensor: " + str(userconfig.SENSOR_TYPE))
    
    for i in range(userconfig.total_streams):
        LOGGER.info("Sensor-%s.ID:%s-%s.Path:%s.",str(i),str(userconfig.STREAM_LIST[i]["id"]),str(userconfig.STREAM_LIST[i]["id_uuid"]),str(userconfig.STREAM_LIST[i]["path"]))

    # Check id for sensors cameraSTREAMS
    for i in range(userconfig.total_streams):
        if (len(userconfig.STREAM_LIST)==0):
            LOGGER.error(" NO CAMERA DEVICE ADDED or OVA was disable. Change sensors.txt and reboot")
            while True:
                pass
    if (len(userconfig.STREAM_LIST)==0 or (userconfig.DISABLE_OVA == True)):
        LOGGER.error(" NO CAMERA DEVICE ADDED or OVA was disable. Change sensors.txt and reboot")
        while True:
            pass
        
    # creating multiprocessing Queue 
    queue_data = Queue()
    
    # Thread for consumer (Send data to cloud)
    sendData_toCloud = Process(name='data_sendToCloud',target=sendData_process,args=(queue_data,))
    sendData_toCloud.setDaemon(True)
    sendData_toCloud.start()

    # Thread for producer (Image processing)
    modules.ImageProcessing.run_detections(
        weights="weigth/" + 'yolov5s.pt',  # model.pt path(s)
        #source= 'data/images',  # file/dir/URL/glob, 0 for webcam
        source= "../intemp/streams.txt",
        data='data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device=0,  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=[0,2],  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels 
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        queue=queue_data,
    )
    
    LOGGER.info("###################################")
    LOGGER.info("Sistema Finalizado")
    LOGGER.info("###################################")
    LOGGER.info("###################################")
    