
from flask import Flask, send_file, request, jsonify, session, make_response
import os
import io
import zipfile
from openai import OpenAI
from flask_cors import CORS
import json


app = Flask(__name__)
app.secret_key = 'your_secret_key'

CORS(app)
#app.config['SECRET_KEY'] = 'your_secret_key'
api_key = ''  # Replace 'your-api-key' with your actual API key
client = OpenAI(api_key=api_key)

@app.route('/upload-zip', methods=['POST'])
def upload_zip():
    # Check if the POST request contains a file
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    zip_file = request.files['file']

    print(zip_file)
    messages=[]
    #session['messages']=messages
    flaskResponse = make_response("Cookie set!")

    # Check if the file has a name and ends with .zip
    if zip_file.filename == '' or not zip_file.filename.endswith('.zip'):
        return jsonify({'error': 'Invalid file format. Please upload a .zip file'}), 400

    try:
        # Read the zip file contents into memory
        zip_data = io.BytesIO(zip_file.read())

        # Extract the contents of the zip file
        with zipfile.ZipFile(zip_data, 'r') as zip_ref:
            file_contents = {}
            
            messages=[#{"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                      {"role": "user", "content": "Please analyze the the java project which I will be sending each file one by one along with the file path"}]
          
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                #response_format={ "type": "json_object" },
                messages=messages,
                temperature=1,
                max_tokens=4096,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
              )
            #print(response)
            print(response.choices[0].message.content)
            ob={"role": "assistant", "content": response.choices[0].message.content}
            messages.append(ob);
            #print("messages ", messages)
            for file_info in zip_ref.infolist():
                with zip_ref.open(file_info) as file:
                    print(file_info.filename)
                    if not file_info.filename.endswith(".java"):
                        continue
                    if file_info.filename.startswith("__MACOSX"):
                        continue
                    content = file.read().decode('utf-8', errors='ignore')
                    file_contents[file_info.filename] = content
                    ob={"role": "user", "content": "providing the file path is "+file_info.filename+ " and its code is "+ content}
                    messages.append(ob)
                    #print("messages ", messages)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        #response_format={ "type": "json_object" },
                        messages=messages,
                        temperature=1,
                        max_tokens=4096,
                        top_p=1,
                        frequency_penalty=0,
                        presence_penalty=0
                      )
                    print(response.choices[0].message.content)
                    ob={"role": "assistant", "content": response.choices[0].message.content}
                    messages.append(ob)
            
            #session['messages']=messages
            #flaskResponse.set_cookie('my_cookie', messages)
            with open('data.json', 'w') as file:
                json.dump(messages, file)
            print("success")
            return "success"

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


@app.route('/summerize', methods=['GET'])
def summerize():
    promptMessages=[]
    with open('data.json', 'r') as file:
        promptMessages = json.load(file)

   
    ob={"role": "user", "content": "please provide summerization of each file and provide the functionality the whole java project by using the code and the file paths provided in the previous prompts"}
    #ob={"role": "user", "content": "please provide the code entire endpoint flow(controller, service,service impl, helper) for deleting the item in fridge by using the code and the file paths provided in the previous prompts"}
    promptMessages.append(ob)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
                #response_format={ "type": "json_object" },
        messages=promptMessages,
        temperature=1,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print("final response ", response.choices[0].message.content)
    return response.choices[0].message.content

@app.route('/bug-fix', methods=['POST'])
def findRCAandFix():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    file_content=file.read().decode('utf-8')
    promptMessages=[]
    with open('data.json', 'r') as file:
        promptMessages = json.load(file)
    ob={"role": "user", "content": "please provide the root cause analysis and provide code fix with lable as suggested code for the issue mentioned in logs  by using the code and the file paths provided in the previous prompts \n  logs: " + file_content}
    promptMessages.append(ob)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
                #response_format={ "type": "json_object" },
        messages=promptMessages,
        temperature=1,
        max_tokens=4096,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    print("final response ", response.choices[0].message.content)
    return response.choices[0].message.content


if __name__ == '__main__':
    app.run(debug=True)