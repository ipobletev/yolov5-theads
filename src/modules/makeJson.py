import uuid
import json
from os import path
import userconfig
from enum import Enum

class EventTypes(Enum):
    PERSONA_DETECTADA = "PERSONA_DETECTADA"
    AGLOMERACION_PLAZA = "AGLOMERACION_PLAZA"
    #AUTO_DETENIDO = "AUTO_DETENIDO"

class json_data:
    
    # Initialize json parameters
    class value:
        class frames:
            class inferences:
                class data:
                    class bounding_box:
                        xmin = 0
                        ymin = 0
                        xmax = 0
                        ymax = 0
                    #Content of data
                    object = ""
                    confidence = ""   
                    bounding_box=bounding_box()
                #Content of inferences
                id = ""
                type = ""
                data=data()
            #Content of frame
            id = ""
            url = ""
            timestamp = 0
            resolution = [0.0]
            inferences=inferences()
        #Content of value
        id = ""
        type = ""
        device_id = ""
        device_type = userconfig.DEVICE_TYPE
        sensor_id = ""
        sensor_type = userconfig.SENSOR_TYPE
        timestamp = 0
        schema_version = ""
        frames=frames()

    #Json content
    key = ""
    value = value()

    # others
    json_content = ""
    filename = ""
    listJson = {'records': []}

    # Initialize json frame
    def __init__(self):
        self.json_content = self.jsonDump()
    
    # Update json parameters with new data
    @classmethod
    def update(self,z,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t):
        self.key = z
        self.value.id = a
        self.value.type = b
        self.value.device_id = c
        self.value.device_type = d
        self.value.sensor_id = e
        self.value.sensor_type = f
        self.value.timestamp = g
        self.value.schema_version = h
        self.value.frames.id = i
        self.value.frames.url = j
        self.value.frames.timestamp = k
        self.value.frames.resolution = l
        self.value.frames.inferences.id = m
        self.value.frames.inferences.type = n
        self.value.frames.inferences.data.object = o
        self.value.frames.inferences.data.confidence = p
        self.value.frames.inferences.data.bounding_box.xmin = self.limitnumber(q,0.0,1.0)
        self.value.frames.inferences.data.bounding_box.ymin = self.limitnumber(r,0.0,1.0)
        self.value.frames.inferences.data.bounding_box.xmax = self.limitnumber(s,0.0,1.0)
        self.value.frames.inferences.data.bounding_box.ymax = self.limitnumber(t,0.0,1.0)
        self.json_content = self.jsonDump(self)
        
        #print(self.json_content)
        return self.json_content

    # Get json
    def jsonDump(self):
        return {
            'key' : self.key,
            'value' : {
                'id': self.value.id,
                'type': self.value.type,
                'deviceId': self.value.device_id,
                'deviceType': self.value.device_type,						
                'sensorId': self.value.sensor_id,
                'sensorType': self.value.sensor_type,					
                'timestamp': self.value.timestamp,
                'schemaVersion': self.value.schema_version,
                'frames': [
                    {
                    'id': self.value.frames.id,
                    'url': self.value.frames.url,
                    'timestamp': self.value.frames.timestamp,
                    'resolution': self.value.frames.resolution,
                    'inferences': [
                        # {
                        # 'id': self.value.frames.inferences.id,
                        # 'type': self.value.frames.inferences.type,
                        # 'data': {
                        #     'object': self.value.frames.inferences.data.object,
                        #     'confidence': self.value.frames.inferences.data.confidence,
                        #     'boundingBox': {
                        #     'xmin': self.value.frames.inferences.data.bounding_box.xmin,
                        #     'ymin': self.value.frames.inferences.data.bounding_box.ymin,
                        #     'xmax': self.value.frames.inferences.data.bounding_box.xmax,
                        #     'ymax': self.value.frames.inferences.data.bounding_box.ymax
                        #     }
                        # }
                        # }
                    ]
                    }
                ]
            }
        }

    @classmethod
    def json_clear(self):
        self.listJson.clear()
        self.listJson = {'records': []}

    @classmethod
    def json_append(self,json_path,json_data,id_stream):

        self.filename = json_path
        f = open(self.filename, "w")

        # Check if file exists
        if path.isfile(self.filename) is False:
            raise Exception("File not found")

        try:
            # Read JSON file
            with open(self.filename) as fp:
                self.listJson = json.load(fp)

            # Verify existing list
            #print(listJson)
            #print(type(listJson))
        except:
            pass

        self.listJson["records"].append(json_data)
        
        # Verify updated list
        #print(self.listJson)
        
        with open(self.filename, 'w') as json_file:
            json.dump(self.listJson, json_file,indent=4,separators=(',',': '))


    def makeJson(id_stream,key_uuid,timestamp,resolution,list_objects):

        #General
        key           = key_uuid
        id            = key_uuid
        type          = EventTypes.PERSONA_DETECTADA.value
        deviceId      = userconfig.DEVICE_ID
        deviceType    = userconfig.DEVICE_TYPE
        sensorId      = userconfig.STREAM_LIST[id_stream]["id_uuid"]
        sensorType    = userconfig.SENSOR_TYPE
        schemaVersion = userconfig.SCHEMA_VERSION
        #Other Frame
        frame_id      = str(uuid.uuid4())

        json_content = json_data.update(
            key,
            id,
            type,
            deviceId,
            deviceType,
            sensorId,
            sensorType,
            timestamp,
            schemaVersion,
            frame_id,
            "",           
            timestamp,
            resolution,
            "",
            "",
            "",
            0,
            0,
            0,
            0,
            0
        )

        #Inferences
        for i,object in enumerate(list_objects):
            #class_id=object[0]
            class_name=object[1]
            confidence=object[2]
            relative_box=object[3]

            inference_object=""
            if(class_name=="person"):
                inference_object   = "person"
            if(class_name=="car"):
                inference_object   = "car"

            inference_id           = str(uuid.uuid4())  
            inference_type         = "DETECTION"
            inference_confidence   = confidence   

            json_content["value"]["frames"][0]["inferences"].append({'id': '', 'type': '', 'data': {'object': '', 'confidence': 0, 'boundingBox': {}}})
            json_content["value"]["frames"][0]["inferences"][i]["id"]=inference_id
            json_content["value"]["frames"][0]["inferences"][i]["type"]=inference_type
            json_content["value"]["frames"][0]["inferences"][i]["data"]["object"]=inference_object
            json_content["value"]["frames"][0]["inferences"][i]["data"]["confidence"]=inference_confidence
            json_content["value"]["frames"][0]["inferences"][i]["data"]["boundingBox"]["xmin"]=relative_box[0]
            json_content["value"]["frames"][0]["inferences"][i]["data"]["boundingBox"]["ymin"]=relative_box[1]
            json_content["value"]["frames"][0]["inferences"][i]["data"]["boundingBox"]["xmax"]=relative_box[2]
            json_content["value"]["frames"][0]["inferences"][i]["data"]["boundingBox"]["ymax"]=relative_box[3]

        return json_content

    def limitnumber(number,min,max):
        if number < min:
            number = min
        if number > max:
            number = max
        return number