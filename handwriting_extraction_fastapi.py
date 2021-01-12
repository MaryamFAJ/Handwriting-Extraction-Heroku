from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import time
import requests
import uvicorn
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import os
import ffmpeg
import speech_recognition as sr

subscription_key = "9f4ab505de56495da6aa7a78a3c9cb60"
endpoint = "https://ocr-handwriting-extraction.cognitiveservices.azure.com/"

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Get an image with handwritten text
remote_image_handw_text_url = "https://github.com/TochiEbere/Hamoye/blob/master/HandwritingTest.jpg?raw=true"


#function defining the input data type
class fn(BaseModel):
    url: str

app= FastAPI()

@app.post('/predict handwriting url')
def predict_(data: fn):
    data = data.dict()
    url = data['url']
    dt = computervision_client.read(url,  raw=True)
    operation_location_remote = dt.headers["Operation-Location"]
    # Grab the ID from the URL
    operation_id = operation_location_remote.split("/")[-1]

    # Call the "GET" API and wait for it to retrieve the results 

    while True:
        get_handw_text_results = computervision_client.get_read_result(operation_id)
        if get_handw_text_results.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # Print the detected text, line by line
    sentences = []
    if get_handw_text_results.status == OperationStatusCodes.succeeded:
        for text_result in get_handw_text_results.analyze_result.read_results:
            for line in text_result.lines:
                sentences.append(line.text )
    #             print(line.text)
    #             print(line.bounding_box)
    return [line for line in sentences]

@app.post('/predict handwriting local images')
async def predict_(Image: UploadFile = File(...)):
    
    # Call API with image and raw response (allows you to get the operation location)
    recognize_handwriting_results = computervision_client.read_in_stream(Image.file, raw=True)
    # Get the operation location (URL with ID as last appendage)
    operation_location_local = recognize_handwriting_results.headers["Operation-Location"]
    # Take the ID off and use to get results
    operation_id_local = operation_location_local.split("/")[-1]


    while True:
        recognize_handwriting_result = computervision_client.get_read_result(operation_id_local)
        if recognize_handwriting_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    # Print the detected text, line by line
    sentences = []
    if recognize_handwriting_result.status == OperationStatusCodes.succeeded:
        for text_result in recognize_handwriting_result.analyze_result.read_results:
            for line in text_result.lines:
                sentences.append(line.text)
    
    return [line for line in sentences]

@app.post('/Extract text from video')
async def predict_(Video: UploadFile = File(...)):
    command2mp3 = "ffmpeg -i Video.file Bolna.mp3"
    command2wav = "ffmpeg -i Bolna.mp3 Bolna.wav"

#execute video conversion commands

    os.system(command2mp3)
    os.system(command2wav)

#load wav file
    r = sr.Recognizer()
    with sr.AudioFile('Bolna.wav') as source:
        audio = r.record(source, duration=120) 
    return (r.recognize_google(audio))



#if __name__=="__handwriting_extraction_fastapi__":
#    uvicorn.run(app, host='127.0.0.1', port=8000)


