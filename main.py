import os
import json
import re

from flask import Flask, request, jsonify
from google import genai
from PIL import Image
import io

app = Flask(__name__)

client = genai.Client(api_key = os.environ.get("GEMINI_API_KEY"))


def cleanString(text):
    text = text.replace('```json', '').replace('```', '').strip()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def splitInitialResult(text):
    dictValue = {}

    for i in text.split(','):
        x = i.split(':')
        col = x[0].split('"')[1]
        num = x[1]

        dictValue[col] = num

    return dictValue

def splitResultValue(dictVal):
    resDict = {}

    divider = dictVal['serving-size']
    divider = divider.split('"')
    divider = divider[1].split('g')
    divider = int(divider[0])
        
    for i in dictVal:
        if i == 'serving-size': continue
        else:
            try:
                resDict[i+'_1g'] = round(float(dictVal[i].strip())/divider, 4)
            except ValueError:
                value = dictVal[i].split('}')
                value = float(value[0].strip())
                resDict[i+'_1g'] = round(value/divider, 4)
    return resDict

@app.route('/', methods=['GET'])
def check():
    return jsonify({'status':'ready'})

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['image']

    image = Image.open(file)

    prompt = (
        "Transcribe the nutrition facts table in this image and output the data "
        "as a single **JSON object**. Use keys like 'serving-size', 'energy-kcal', 'fat', 'carbohydrates', 'proteins', 'saturated-fat', 'trans-fat', 'sugars', 'added-sugars', 'sodium', 'salt', and 'fiber'. "
        "Do not include any text outside of the JSON object."
        "If the values are not in the image, fill the values with 0"
        "Pay attention to the unit, normalize the unit so it's stated in g (gram) instead of mg (miligram)"
    )

    result = client.models.generate_content(
        model='gemini-2.5-flash', 
        contents=[prompt, image]
    )

    text = result.text
    text = cleanString(text)

    splitDict = splitInitialResult(text)
    resDict = splitResultValue(splitDict)

    return resDict

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    app.run(host='0.0.0.0', port=port)


