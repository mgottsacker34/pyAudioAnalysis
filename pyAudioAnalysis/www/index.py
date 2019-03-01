import os
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory
from werkzeug.utils import secure_filename

TEMPLATES_AUTO_RELOAD = True

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['wav'])

uploaded_files = []
for (dirpath, dirnames, filenames) in os.walk(UPLOAD_FOLDER):
    uploaded_files.extend(filenames)
    break

app = Flask(__name__)
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
            flash('No file part')
            return redirect(request.url)
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
