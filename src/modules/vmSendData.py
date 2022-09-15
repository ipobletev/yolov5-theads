import json
import logging
import uuid
import requests
import userconfig
from typing import Any, List
from utils.general import LOGGER

class vmSendData:

    def sendImageToGPU(in_imagepath,uuid,url):

        namefile = uuid + '.png'
        headers = {}
        payload = {
            "id": namefile,
            "url": url
        }
        files=[
        ('image',(namefile,open(in_imagepath,'rb'),'image/png'))
        ]

        try:
            if userconfig.ENABLE_SENDTO_GPU == True:
                LOGGER.info("***Envio de imagen a GPU***")
                resource = requests.request("POST", url, headers=headers, data=payload, files=files)

            LOGGER.info(f"URL: {url}")
            #LOGGER.info(f"HEADERS: {headers}")
            LOGGER.info(f"PAYLOAD: {payload}")

            if userconfig.ENABLE_SENDTO_GPU == True:
                LOGGER.info(f"RESPONSE: {resource.text}")
        except:
            LOGGER.info("Error de envio")

    def publish_JsonToGPU(in_jsonpath,gpu_name_image,url):

        # Read the json file
        file = open(in_jsonpath)
        events = json.load(file)

        # Add the url image name
        for event in events['records']:
            temp_uuid = str(uuid.uuid4())
            event['key'] = temp_uuid
            event['value']['id'] = temp_uuid
            event['value']['frames'][0]['url'] = url
            event['value']['frames'][0]['id'] = gpu_name_image
        
        # Send jsons
        headers = {
            "Content-Type": "application/json",
        }
        payload = events
        try:
            if userconfig.ENABLE_SENDTO_GPU == True:
                LOGGER.info("***Envio de json a GPU***")
                resource = requests.post(url,headers=headers,data=json.dumps(payload))

            LOGGER.info(f"URL: {url}")
            #LOGGER.info(f"HEADERS: {headers}")
            LOGGER.info(f"PAYLOAD: {payload}")

            if userconfig.ENABLE_SENDTO_GPU == True:
                LOGGER.info(f"RESPONSE: {resource.text}")
        except:
            LOGGER.info("Error de envio")
