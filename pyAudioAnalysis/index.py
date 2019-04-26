import os
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
import json
import wave
import contextlib
from werkzeug.utils import secure_filename
from pyAudioAnalysis import silenceUtil

TEMPLATES_AUTO_RELOAD = True

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['wav'])

uploaded_files = []

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.use_reloader=False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# called when web app is first run
def getFilesInFolder():
    for (dirpath, dirnames, filenames) in os.walk(UPLOAD_FOLDER):
        uploaded_files.extend(filenames)
        break
        
# called when list gets updated
def getNewFilesInFolder():
    for (dirpath, dirnames, filenames) in os.walk(UPLOAD_FOLDER):
        for file in filenames:
            if file not in uploaded_files:
                uploaded_files.append(file)
        break
        
def computeLengthOfFile(wavFile):
    with contextlib.closing(wave.open(wavFile,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        print(duration)
        return duration
        


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
           filename not in uploaded_files

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            print('no file part')
            print(request.form)
            # flash('No file part')
            # return redirect(request.url)
            if 'silenceremoval' in request.form['analysis']:
                fileToProcess = './uploads/' + request.form['fileToProcess']
                if '.wav' not in fileToProcess:
                    flash('ERROR: Please enter a .wav file from the list above as the file to process.')
                    return render_template('index.html', data=uploaded_files)
                if not os.path.isfile(fileToProcess):
                    flash('ERROR: Please enter a .wav file from the list above as the file to process.')
                    return render_template('index.html', data=uploaded_files)
                print('Calling silenceUtil...')
                processedFile = silenceUtil.removeSilence(fileToProcess, 0.1, 0.1)
                
                if (processedFile):
                    getNewFilesInFolder()
                    return render_template('index.html', data=uploaded_files)
                else:
                    flash('ERROR: Silence removal errored.')
                    return render_template('index.html', data=uploaded_files)
            elif 'speakerdiarization' in request.form:
                print('Speaker diarization')
                return render_template('index.html', data=uploaded_files)
            elif 'mfclassification' in request.form:
                print('Male/Female Classification')
                return render_template('index.html', data=uploaded_files)
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
                num_speakers = 5 # should get from user input
                
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
                uploaded_files.append(filename)
                return render_template('index.html', data=uploaded_files)
                # return redirect(url_for('uploaded_file',
                #                         filename=filename))


    return render_template('index.html', data=uploaded_files)
