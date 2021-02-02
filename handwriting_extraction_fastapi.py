from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
import os
# import ffmpeg
import speech_recognition as sr
import shutil


import time
import requests
import uvicorn
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
#from textblob import TextBlob

subscription_key = "9f4ab505de56495da6aa7a78a3c9cb60"
endpoint = "https://ocr-handwriting-extraction.cognitiveservices.azure.com/"

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Get an image with handwritten text
remote_image_handw_text_url = "https://github.com/TochiEbere/Hamoye/blob/master/HandwritingTest.jpg?raw=true"


#function defining the input data type
class fn(BaseModel):
    url: str

app= FastAPI()

@app.post('/Extract text from cloud image')
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
#     sentences = ''
    if get_handw_text_results.status == OperationStatusCodes.succeeded:
        for text_result in get_handw_text_results.analyze_result.read_results:
            for line in text_result.lines:
                sentences = ''.join(line.text)
    #             print(line.text)
    #             print(line.bounding_box)
    
    text = TextBlob(sentences)

    return str(text.correct())

@app.post('/Extract text from local image')
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
                correct_line = TextBlob(line.text).correct()
                sentences.append(str(correct_line))
    
    return [line for line in sentences]

@app.post('/Extract text from video')
def predict_video(Video: UploadFile = File(...)):

    with open("file.mp4", "wb") as buffer:
        shutil.copyfileobj(Video.file, buffer)

    # full_path = os.path.abspath(Video.filename)
    command2mp3 = 'ffmpeg -i ' + 'file.mp4' + " audio.mp3"
    command2wav = "ffmpeg -i audio.mp3 wave.wav"
    command2del = 'del audio.mp3 wave.wav file.mp4'

    os.system(command2mp3)
    os.system(command2wav)

    r = sr.Recognizer()
    with sr.AudioFile('wave.wav') as source:
        audio = r.record(source, duration=120) 
    
    os.system(command2del) # delete converted files

    return (r.recognize_google(audio, language='en'))


@app.post('/Extract text from audio')
def predict_audio(Audio: UploadFile = File(...)):

    with open("file.mp3", "wb") as buffer:
        shutil.copyfileobj(Audio.file, buffer)

    command2wav = "ffmpeg -i " + "file.mp3" + " audio.wav"
    command2del = 'del file.mp3 audio.wav'

    os.system(command2wav)

    r = sr.Recognizer()
    with sr.AudioFile('audio.wav') as source:
        audio = r.record(source,duration=120) 
    
    os.system(command2del)  # deleted converted files

    return (r.recognize_google(audio))

#if __name__=="__handwriting_extraction_fastapi__":
#    uvicorn.run(app, host='127.0.0.1', port=8000)


