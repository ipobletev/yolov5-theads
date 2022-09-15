# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Run YOLOv5 detection inference on images, videos, directories, globs, YouTube, webcam, streams, etc.

Usage - sources:
    $ python detect.py --weights yolov5s.pt --source 0                               # webcam
                                                     img.jpg                         # image
                                                     vid.mp4                         # video
                                                     path/                           # directory
                                                     'path/*.jpg'                    # glob
                                                     'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                     'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python detect.py --weights yolov5s.pt                 # PyTorch
                                 yolov5s.torchscript        # TorchScript
                                 yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                 yolov5s.xml                # OpenVINO
                                 yolov5s.engine             # TensorRT
                                 yolov5s.mlmodel            # CoreML (macOS-only)
                                 yolov5s_saved_model        # TensorFlow SavedModel
                                 yolov5s.pb                 # TensorFlow GraphDef
                                 yolov5s.tflite             # TensorFlow Lite
                                 yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
"""

import argparse
from datetime import datetime, timezone
import os
import platform
import sys
from pathlib import Path
import uuid
import torch
import torch.backends.cudnn as cudnn

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode
from time import time
from modules.makeJson import json_data
import userconfig

N_ITEMS = userconfig.total_streams
SECUENCE_TEMP = userconfig.TIME_SECUENCE_TOPROCESING_IMAGEN

last_time = [time() for x in range(N_ITEMS)]

def ready_tosave(stream):
    # Reach each SECUENCE_TEMP
    if(time() - last_time[stream]) > SECUENCE_TEMP:
        last_time[stream]=time()
        return True
    return False
        
@smart_inference_mode()
def run_detections(
        weights=ROOT / "weigth" / 'yolov5s.pt',  # model.pt path(s)
        source=ROOT / 'data/images',  # file/dir/URL/glob, 0 for webcam
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
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
        queue=[],
):
    try:
        LOGGER.info("############## INIT SETUP INFERENCE ##############")
        list_objects = []
        source = str(source) #streams.txt
        save_img = not nosave and not source.endswith('.txt')  # save inference images
        is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
        is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
        webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
        if is_url and is_file:
            source = check_file(source)  # download

        # Load model
        device = select_device(device) # CPU or GPU
        model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
        stride, names, pt = model.stride, model.names, model.pt
        imgsz = check_img_size(imgsz, s=stride)  # check image size

        # Dataloader
        if webcam:
            timestamp = datetime.now(timezone.utc).isoformat()
            view_img = check_imshow()
            cudnn.benchmark = True  # set True to speed up constant image size inference
            dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
            bs = len(dataset)  # batch_size
        else:
            dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
            bs = 1  # batch_size
        vid_path, vid_writer = [None] * bs, [None] * bs

        # Run inference
        model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
        
        LOGGER.info("###########################################")
        
        for path, im, im0s, vid_cap, s in dataset:
            #print(path) # Array of all streams.
            with dt[0]:
                im = torch.from_numpy(im).to(device)
                im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
                im /= 255  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim

            # Inference
            with dt[1]:
                visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
                pred = model(im, augment=augment, visualize=visualize)

            # NMS
            with dt[2]:
                pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
            
            ###### ALL STREAMS
            frame_uuid = str(uuid.uuid4())
            # Process predictions
            for i, det in enumerate(pred):  # per image
                ###### ONE STREAM
                list_objects.clear()
                seen += 1
                if webcam:  # batch_size >= 1
                    p, im_raw, frame = path[i], im0s[i].copy(), dataset.count
                    s += f'{i}: '
                else:
                    p, im_raw, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

                im_wbb = im_raw.copy()
                
                p = Path(p)  # to Path.
                path_stream = str(p.stem)
                id_stream = str(i)
                gn = torch.tensor(im_wbb.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                annotator = Annotator(im_wbb, line_width=line_thickness, example=str(names))
                if len(det):
                    # Rescale boxes from img_size to im_wbb size
                    det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im_wbb.shape).round()

                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        
                        #absolute box
                        x_abs = xyxy[0].item()
                        y_abs = xyxy[1].item()
                        w_abs = xyxy[2].item()
                        h_abs = xyxy[3].item()
                        box_absolute = [x_abs,y_abs,w_abs,h_abs]
                        
                        # relative box
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()
                        x = xywh[0]
                        y = xywh[1]
                        w = xywh[2]
                        h = xywh[3]
                        box_relative = [x,y,w,h]
                        
                        # Class
                        c = int(cls)  # integer class
                        
                        # List all items
                        objs = [c,names[c],conf.item(),box_relative,box_absolute]
                        list_objects.append(objs)
                        #print(objs)
                        
                        #Add bb to image
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        frame_wbb = annotator.box_label(xyxy, label, color=colors(c, True))

                # Stream results
                frame_wbb = annotator.result()
                if view_img:
                    if platform.system() == 'Linux' and p not in windows:
                        windows.append(p)
                        cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                        cv2.resizeWindow(str(p), frame_wbb.shape[1], frame_wbb.shape[0])
                    cv2.imshow(str(p), frame_wbb)
                    cv2.waitKey(1)  # 1 millisecond

                # Save results to queue
                # Each SECUENCE_TEMP and if we have detections
                flag_readytosend = ready_tosave(i) == True and len(det) != 0
                if flag_readytosend:
                    
                    ###### Acquire frame
                    cloud_frame_width, cloud_frame_height = im_wbb.shape[1], im_wbb.shape[0]
                    
                    ###### Images
                    cv2.imwrite("temp/"+ "temp_wbb_" + frame_uuid + "_" + id_stream + ".png",im_wbb)
                    cv2.imwrite("temp/"+ "temp_raw_" + frame_uuid + "_" + id_stream + ".png",im_raw)
                    
                    ###### Json
                    json_path = 'temp/temp_event_' + frame_uuid + "_" + id_stream + '.json'
                    
                    # Make json file from data
                    json_data.json_clear()
                    json_content = json_data.makeJson(int(id_stream),frame_uuid,timestamp,[cloud_frame_width,cloud_frame_height],list_objects)

                    # Detect interest objects
                    cont_person=0
                    cont_car=0
                    for interest_obj in list_objects:
                        if interest_obj[1] == 'person':
                            cont_person +=1
                        if interest_obj[1] == 'car':
                            cont_car +=1

                    if(cont_person == 0 and cont_car > 0):
                        LOGGER.debug('Auto y persona')
                        json_content["value"]["type"] = "AUTO_DETECTADO"
                    if(cont_person > 0 and cont_car > 0):
                        LOGGER.debug('Auto y persona')
                        json_content["value"]["type"] = "AUTO_Y_PERSONA_DETECTADA"

                    #Make json to file
                    json_data.json_append(json_path,json_content,int(id_stream))
                    
                    # Add to queue
                    #queue.append(frame_uuid)
                    queue.put(frame_uuid)
                    
                    # Relevants deteccions
                    LOGGER.info("Stream: " + id_stream + " Path: " + path_stream)
                    LOGGER.info("Person: " + str(cont_person))
                    LOGGER.info("Car: " + str(cont_car))
                    LOGGER.info("------------------------------------------------")
                
                ##### END ONE PROCESSING STREAM
            
            ###### END ALL STREAMS PROCESSING
            
            # Print time (inference-only)
            #print(list_objects)
            #LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")
            
            #Image speed
            if flag_readytosend:
                t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
                LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
                LOGGER.info("###########################################")
                
    except KeyboardInterrupt:
        cv2.destroyAllWindows()