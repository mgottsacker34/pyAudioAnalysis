import os
import glob
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
import json
import wave
import contextlib
import re

from werkzeug.utils import secure_filename
from pyAudioAnalysis import webUtil

TEMPLATES_AUTO_RELOAD = True

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['wav'])

# webdata.uploaded_files = []

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.use_reloader=False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Data structure to store all webapp info. This will be passed to front end.
webdata = {
    "uploaded_files": [],
    "ratio_male": 0.0,
    "ratio_female": 0.0,
    "img_src": "",
    "type": "none",
    "name": "",
    "m_time": 0,
    "f_time": 0,
    "total_time": 0
}

# Store list of uploaded files. Called when web app is first run
def getFilesInFolder():
    for (dirpath, dirnames, filenames) in os.walk(UPLOAD_FOLDER):
        for file in filenames:
            if file not in webdata["uploaded_files"] and file.endswith(".wav"):
                webdata["uploaded_files"].append(file)
        break

# Get length (in seconds) of audio file   
def computeLengthOfFile(wavFile):
    with contextlib.closing(wave.open(wavFile,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        print('audio file length computed for', wavFile, ': ', duration)
        return duration

# loop through records in JSON file and find the one to update
def findRecordAndUpdate(filename, updateMode, mf_data=[0,0,0,0]):

    # For debugging...
    print('file to find and update: ', filename)
    print('update mode:             ', updateMode)
    print('mf_data:                 ', mf_data)

    with open("reports.json", "r") as jsonFile:
        data = json.load(jsonFile)
        
    # Iterate through records in JSON file and find the right one to update.
    for record in data["individual_report_data"]:
        if record["basename"] == filename:
            # If desired action is get new length after silence removed, compute length.
            if updateMode == "silenceRemoved":
                # Get filename with -nosilence appended.
                filename = re.findall('.*[^.wav]', filename)[0] + '-nosilence.wav'
                # Get full file path.
                fullFilePath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                record["lengthWithoutSilence"] = computeLengthOfFile(fullFilePath)
                
            # TODO: Update m/f data in report record.
            # Right now, it takes an array as a parameter, so the mf_data values MUST BE IN THIS ORDER.
            # We could also use a dict, so that order wouldn't matter. Whatever works.
            elif updateMode == "mfClassified":
                record["m_speakingTime"] = mf_data[0]
                record["f_speakingTime"] = mf_data[1]
                record["m_speakingRatio"] = mf_data[2]
                record["f_speakingRatio"] = mf_data[3]
                
    # write resultant data to file
    with open("reports.json", "w") as jsonFile:
        json.dump(data, jsonFile, indent=4)

getFilesInFolder()

@app.route('/uploads')
def autoload(filename):
    if filename != '':
        return render_template('index.html', name = filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS and \
           filename not in webdata["uploaded_files"]

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has a file. Form submission will not have file.
        if 'file' not in request.files:
        
            print('--- Received form data:')
            print(request.form)
            print('---')
            
            # TODO: Process all records in reports.json to get aggregate stats
            if request.form['processaction'] == 'Statistics For All Files':
            
                print('Processing all files in reports.json...')
            
        
                # Possible way to do this:
                # Iterate through records in the JSON using method similar to in findRecordAndUpdate()
                m_total = 0
                f_total = 0
                total_time = 0
                m_total_ratio = 0
                f_total_ratio = 0
                
                with open("reports.json", "r") as jsonFile:
                    data = json.load(jsonFile)
                    
                    for record in data["individual_report_data"]:
                        m_total += record["m_speakingTime"]
                        f_total += record["f_speakingTime"]
                        total_time += record["lengthWithoutSilence"]
                    
                m_total_ratio = m_total/total_time
                f_total_ratio = f_total/total_time
                
                # Write values to reports.json similar to in findRecordAndUpdate(). You will not need
                # find the record, as the "aggregate_report_data" is the only object of its kind and
                # is not in an array. I did not test this, but Something like:
                
                with open("reports.json", "r") as jsonFile:
                    data = json.load(jsonFile)
                    
                data["aggregate_report_data"]["m_total_ratio"] = m_total_ratio 
                
                data["aggregate_report_data"]["f_total_ratio"] = f_total_ratio
                
                data["aggregate_report_data"]["m_total_time"] = m_total
                
                data["aggregate_report_data"]["f_total_time"] = f_total
                
                data["aggregate_report_data"]["total_time"] = total_time
                            
                # write resultant data to file
                with open("reports.json", "w") as jsonFile:
                    json.dump(data, jsonFile, indent=4)
                
                
                # Create visualization from ratios
                # update webdata.img_src
                
                # Refresh webpage with updated image
                return render_template('index.html', data=webdata)
                
            if request.form['processaction'] == "Remove Silence":
            
                fileToProcess = './uploads/' + request.form['fileToProcess']
                # Handle malformed user input
                if '.wav' not in fileToProcess:
                    flash('ERROR: Please enter a .wav file from the list above as the file to process.')
                    return render_template('index.html', data=webdata)
                if not os.path.isfile(fileToProcess):
                    flash('ERROR: Please enter a .wav file from the list above as the file to process.')
                    return render_template('index.html', data=webdata)
                    
                print('Calling silenceUtil...')
                
                processedFile = webUtil.removeSilence(fileToProcess, 0.1, 0.1)
                
                # Find file record in records.json and update its lengthWithoutSilence
                findRecordAndUpdate(request.form['fileToProcess'], "silenceRemoved")
                
                # Refresh file list after adding the -nosilence file
                if (processedFile):
                    getFilesInFolder()
                    return render_template('index.html', data=webdata)
                else:
                    flash('ERROR: Silence removal failed.')
                    return render_template('index.html', data=webdata)
                
            elif request.form['processaction'] == "Classify Male/Female":
                # TODO: Run mf_classification and do something with results
                print('Male/Female Classification')
                fileToProcess = './uploads/' + request.form['fileToProcess']
                
                # Call to webUtil mf_classify function. Should return speaking times and 
                # percentages of males and females.
                [m_ratio, f_ratio, unk_ratio, m_time, f_time, unk_time] = webUtil.mf_classify(fileToProcess)
                majorKeys = [m_ratio,f_ratio,unk_ratio,m_time,f_time,unk_time]
                # TODO: Write total times and ratios to reports.json file
                #webUtil.produceVisuals(fileToProcess,majorKeys)
                # TODO: Create visualization with ratios
                webdata["img_src"] = webUtil.produceVisuals(fileToProcess,majorKeys)
                
                print("img_src", webdata["img_src"])
                # TODO: Send visualization to frontend.
		
                # This will probably be in the form of setting webdata.img_src to the name of 
                # the file generated from the visualization code.

                # render_template() is called to refresh the index.html page. It sends the
                # webdata object to index.html so that we can use its objects in the HTML
                # code. See my example of iterating through the list of uploaded files 
                # on the frontend.
                return render_template('index.html', data=webdata)
        else:
            file = request.files['file']
            # Check if no file selected
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                fullFilePath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(fullFilePath)
                
                with open("reports.json", "r") as jsonFile:
                    data = json.load(jsonFile)

                reports_length = len(data["individual_report_data"])
                length = computeLengthOfFile(fullFilePath)
                
                # TODO: Get num_speakers from user input box on file upload
                num_speakers = 5
                
                new_file_data = {
                        "basename": filename,
                        "length": length,
                        "num_speakers": num_speakers,
                        "lengthWithoutSilence": 0,
                        "m_speakingTime": 0,
                        "f_speakingTime": 0,
                        "m_speakingRatio": 0,
                        "f_speakingRatio": 0
                     }
                data["individual_report_data"].append(new_file_data)

                with open("reports.json", "w") as jsonFile:
                    json.dump(data, jsonFile, indent=4)
                
                json.dumps(data, indent=4)
                webdata["uploaded_files"].append(filename)
                return render_template('index.html', data=webdata)
                # return redirect(url_for('uploaded_file',
                #                         filename=filename))


    return render_template('index.html', data=webdata)
