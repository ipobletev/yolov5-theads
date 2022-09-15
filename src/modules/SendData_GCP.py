from datetime import datetime
import json
from enum import Enum
import userconfig
import os, sys
import time
import jwt
from google.cloud import storage
import requests
from utils.general import LOGGER
PYTHONPATH=os.getcwd() + '/Modules'
sys.path.append(PYTHONPATH)

URL_CLOUD_PRODUCT_IMAGEBUCKET = ""
URL_CLOUD_PRODUCT_JSON = ""

URL_CLOUD_DEVELP_IMAGEBUCKET = ""
URL_CLOUD_DEVELP_JSON = ""

SEND_TO_DEVELOP_CLOUD = (os.getenv('SEND_TO_DEVELOP_CLOUD', 'False') == 'True')

if(SEND_TO_DEVELOP_CLOUD==True):
    STRING_CREDS_P = "creds/creds_dev.json"
else:
    STRING_CREDS_P = "creds/creds.json"
    
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = userconfig.STRING_CREDS_P


class CloudCredentials:
    TOKEN=""

    def __init__(self,credentials_file):
        self.makeCredentials(credentials_file)

    def makeCredentials(self,credentials_file):
        LOGGER.info("---------------------------------------------")
        LOGGER.info("Creando credenciales para la nube")
        LOGGER.info("---------------------------------------------")
        cred = self.load_json_credentials(credentials_file)
        self.TOKEN = self.create_signed_jwt(
            cred["private_key"],
            cred["private_key_id"],
            cred["client_email"],
            "https://www.googleapis.com/auth/cloud-platform"
        )   

    def load_json_credentials(self,filename: str) -> dict:
        """
        Load the Google Service Account Credentials from Json file.
        """
        #print("load_json_credentials -> Start")
        with open(filename, "r", encoding="utf8") as json_file:
            data_json = json.load(json_file)
        #print("load_json_credentials -> End")
        return data_json

    def create_signed_jwt(self,pkey: str, pkey_id: str, email: str, scope: str) -> str:
        """
        Create a Signed JWT from a service account Json credentials file
        This Signed JWT will later be exchanged for an Access Token.
        """
        #print("create_signed_jwt -> Start")

        # Google Endpoint for creating OAuth 2.0 Access Tokens from Signed-JWT
        auth_url = "https://www.googleapis.com/oauth2/v4/token"

        issued = int(time.time())
        expires = issued + 3600*24   # expires_in is in seconds
        # Note: this token expires and cannot be refreshed. The token must be recreated

        # JWT Headers
        additional_headers = {
            "kid": pkey_id,
            "alg": "RS256",
            "typ": "JWT"    # Google uses SHA256withRSA
        }

        # JWT Payload
        payload = {
            "iss": email,       # Issuer claim
            "sub": email,       # Issuer claim
            "aud": auth_url,    # Audience claim
            "iat": issued,      # Issued At claim
            "exp": expires,     # Expire time
            "scope": scope      # Permissions
        }

        # Encode the headers and payload and sign creating a Signed JWT (JWS)
        sig = jwt.encode(payload, pkey, algorithm="RS256", headers=additional_headers)
        #print("create_signed_jwt -> End")
        return sig


class SendDataGCP:

    def sendImageForROI_ToCloud(self,image_tosend,dir, sensor_id):

        LOGGER.info('--')
        if userconfig.SEND_TO_DEVELOP_CLOUD == True:
            LOGGER.info('Send ROI image to cloud to DEVELOP')
            bucket_name = userconfig.URL_CLOUD_DEVELP_IMAGEBUCKET
    
        if userconfig.SEND_TO_DEVELOP_CLOUD == False:
              
            LOGGER.info('Send ROI image to cloud to PRODUCT')
            bucket_name = userconfig.URL_CLOUD_PRODUCT_IMAGEBUCKET
                
        storage_client = storage.Client().from_service_account_json(userconfig.STRING_CREDS_P)

        date = datetime.today().strftime('%Y-%m-%d/%02H%02M')
        dst_blob_name = f"last_capture/{sensor_id}/{date}.jpg"

        url = f"https://storage.cloud.google.com/{bucket_name}/{dst_blob_name}"
        LOGGER.info(url)

        if userconfig.ENABLE_SENDTO_CLOUD == True:
            LOGGER.info("***Envio de imagen a cloud***")
            try:
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(dst_blob_name)
                blob.upload_from_filename(image_tosend)
                LOGGER.info("Envio exitoso.")
            except Exception as error_info:
                LOGGER.error("Error de envio.")
                LOGGER.error(error_info)
        return url

    @classmethod
    def sendImageRawImageToCloud(self,image_tosend,device_id,sensor_id,timestamp,uuid_image,dir):
        status=0
        if userconfig.SEND_TO_DEVELOP_CLOUD == True:
            LOGGER.info('Send Raw image to cloud to DEVELOP')
            bucket_name = userconfig.URL_CLOUD_DEVELP_IMAGEBUCKET
    
        if userconfig.SEND_TO_DEVELOP_CLOUD == False:
            LOGGER.info('Send Raw image to cloud to PRODUCT')
            bucket_name = userconfig.URL_CLOUD_PRODUCT_IMAGEBUCKET
            
        storage_client = storage.Client().from_service_account_json(userconfig.STRING_CREDS_P)

        #print("upload_frame_to_storage -> Start")
        dt_parts = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d').split("-")
        # Ejm: 34cfe98b-a4e8-4de1-931f-f1895fc3822f/2022/03/01/1234e98b-a4e8-4de1-931f-f1895fc3822f/66cff98b-a5e8-4de1-931f-f1895fc38212_example.png
        dst_blob_name = f"{sensor_id}/{dt_parts[0]}/{dt_parts[1]}/{dt_parts[2]}/{device_id}/raw/{uuid_image}.png"
        url = f"https://storage.cloud.google.com/{bucket_name}/{dst_blob_name}"
        LOGGER.info(url)
        if userconfig.ENABLE_SENDTO_CLOUD == True:
            LOGGER.info("***Envio de imagen a cloud***")
            try:
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(dst_blob_name)
                blob.upload_from_filename(image_tosend)
                LOGGER.info("Envio exitoso.")
            except Exception as error_info:
                LOGGER.error("Error de envio.")
                LOGGER.error(error_info)
        return status,url

    def sendImageToCloud(image_tosend,device_id,sensor_id,timestamp,uuid_image,dir):
        status=0
        if userconfig.SEND_TO_DEVELOP_CLOUD == True:
            LOGGER.info('Send wBB image to cloud to DEVELOP')
            bucket_name = userconfig.URL_CLOUD_DEVELP_IMAGEBUCKET

        if userconfig.SEND_TO_DEVELOP_CLOUD == False:
            LOGGER.info('Send wBB image to cloud to PRODUCT')
            bucket_name = userconfig.URL_CLOUD_PRODUCT_IMAGEBUCKET
        
        storage_client = storage.Client().from_service_account_json(userconfig.STRING_CREDS_P)

        dt_parts = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d').split("-")
        # Ejm: 34cfe98b-a4e8-4de1-931f-f1895fc3822f/2022/03/01/1234e98b-a4e8-4de1-931f-f1895fc3822f/66cff98b-a5e8-4de1-931f-f1895fc38212_example.png
        dst_blob_name = f"{sensor_id}/{dt_parts[0]}/{dt_parts[1]}/{dt_parts[2]}/{device_id}/{uuid_image}.png"
        url = f"https://storage.cloud.google.com/{bucket_name}/{dst_blob_name}"
        LOGGER.info(url)

        if userconfig.ENABLE_SENDTO_CLOUD == True:
            LOGGER.info("***Envio de imagen a cloud***")
            try:
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(dst_blob_name)
                blob.upload_from_filename(image_tosend)
                LOGGER.info("Envio exitoso.")
            except Exception as error_info:
                LOGGER.error("Error de envio.")
                LOGGER.error(error_info)
                status=1
        return status,url

    #########################################################

    def publish_JsonToCloud(cloud_imagename_url,in_jsonpath, token: str,dir) -> None:
        status=0
        
        if userconfig.SEND_TO_DEVELOP_CLOUD == True:
            LOGGER.info('Send json to cloud to DEVELOP')
            url = userconfig.URL_CLOUD_DEVELP_JSON
            
        if userconfig.SEND_TO_DEVELOP_CLOUD == False: 
            LOGGER.info('Send json to cloud to PRODUCT')
            url = userconfig.URL_CLOUD_PRODUCT_JSON
                
        # Read the json file
        file = open(in_jsonpath)
        events = json.load(file)

        # Add the url image name
        for event in events['records']:
            event['value']['frames'][0]['url'] = cloud_imagename_url

        # Send jsons
        headers = {
            "Content-Type": "application/vnd.kafka.json.v2+json",
            "Authorization": f"Bearer {token}"
        }
        payload = events
        
        try:
            if userconfig.ENABLE_SENDTO_CLOUD == True:
                LOGGER.info("***Envio de json a cloud***")
                resource = requests.post(url, headers=headers, data=json.dumps(payload))

            LOGGER.info(f"URL: {url}")
            #LOGGER.info(f"HEADERS: {headers}")
            LOGGER.info(f"PAYLOAD: {payload}")

            if userconfig.ENABLE_SENDTO_CLOUD == True:
                LOGGER.info(f"RESPONSE: {resource.text}")
        except:
            LOGGER.error("Error de envio")
            status=1
        
        return status