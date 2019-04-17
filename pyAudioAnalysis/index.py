import os
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename
from pyAudioAnalysis import silenceUtil

TEMPLATES_AUTO_RELOAD = True

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['wav'])

uploaded_files = []
for (dirpath, dirnames, filenames) in os.walk(UPLOAD_FOLDER):
    uploaded_files.extend(filenames)
    break

app = Flask(__name__)
app.config.from_pyfile('config.py')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
                print('calling silenceUtil')
                fileToProcess = './uploads/' + request.form['fileToProcess']
                if '.wav' not in fileToProcess:
                    flash('ERROR: Please enter a .wav file from the list above as the file to process.')
                    return render_template('index.html', data=uploaded_files)
                if not os.path.isfile(fileToProcess):
                    flash('ERROR: Please enter a .wav file from the list above as the file to process.')
                    return render_template('index.html', data=uploaded_files)
                print('Removing silence from ' + fileToProcess)
                silenceUtil.removeSilence(fileToProcess, 0.3, 0.1)
                return render_template('index.html', data=uploaded_files)
            elif 'speakerdiarization' in request.form:
                print('Speaker diarization')
                return render_template('index.html', data=uploaded_files)
            elif 'mfclassification' in request.form:
                print('Male/Female Classification')
                return render_template('index.html', data=uploaded_files)
        else:
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_files.append(filename)
                return render_template('index.html', data=uploaded_files)
                # return redirect(url_for('uploaded_file',
                #                         filename=filename))


    return render_template('index.html', data=uploaded_files)
