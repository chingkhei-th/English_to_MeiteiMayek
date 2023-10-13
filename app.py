from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
import tensorflow as tf
import tensorflow_text
import sentencepiece
import csv
from io import StringIO
import codecs
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

app = Flask(__name__)
app.secret_key = "secretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+mysqlconnector://root:mysqlroot@localhost:3306/Translation'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    english = db.Column(db.VARCHAR(255), nullable=False)
    meitei_mayek = db.Column(db.VARCHAR(255), nullable=False)

    def __init__(self, english, meitei_mayek):
        self.english = english
        self.meitei_mayek = meitei_mayek

@app.route('/', methods=['POST', 'GET'])
def home():

    if request.method == 'POST':
        data = request.json
        input_text = data['text']

        # Load the saved model
        model = tf.saved_model.load(r'D:\Programming\PROJECT\TEST\Mtrans\model')
        # Perform translation using the model
        translated_text = model(input_text).numpy().decode('utf-8')

        return jsonify({'translated': translated_text})

    data = Data.query.first()
    return render_template('translate.html', data=data)

@app.route('/download')
def Index():
    page = request.args.get('page', 1, type=int)

    per_page = 5

    data = Data.query.paginate(page=page, per_page=per_page)
    return render_template("i.html", data=data)

@app.route('/input', methods=['GET', 'POST'])
def input_data():
    if request.method == 'POST':
        english = request.form['english']
        meitei_mayek = request.form['meitei_mayek']
        add_data = Data(english, meitei_mayek)
        db.session.add(add_data)
        db.session.commit()
        flash("Inserted Successful")
        return redirect(url_for('Index'))
    return render_template("input.html")

@app.route('/purge_data', methods=['POST'])
def purge_data():
    # Delete all records from the Data table
    db.session.query(Data).delete()
    db.session.commit()
    flash('Data table purged successfully', "success")
    return redirect(url_for('Index'))

@app.route('/edit/<int:id>')
def edit_data(id):
    data_base = Data.query.get(id)
    return render_template('edit.html', data=data_base)

@app.route('/text_edit', methods=['POST', 'GET'])
def text_edit():
    data_base = Data.query.get(request.form.get('id'))
    data_base.english = request.form['english']
    data_base.meitei_mayek = request.form['meitei_mayek']
    db.session.commit()
    flash('Edit Successful', "success")
    return redirect(url_for('Index'))

@app.route('/delete/<int:id>')
def delete(id):
    data_base = Data.query.get(id)
    db.session.delete(data_base)
    db.session.commit()
    flash('Deleted Successful', "success")
    return redirect(url_for('Index'))

@app.route('/download_csv')
def download_csv():
    data = Data.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['English', 'Meitei Mayek'])
    for row in data:
        writer.writerow([row.english, row.meitei_mayek])
    output.seek(0)
    encoded_output = codecs.BOM_UTF8 + output.getvalue().encode('utf-8')
    flash('Download Successful', "success")
    return Response(
        encoded_output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=data.csv",
            "Content-Encoding": "utf-8"
        }
    )

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            sentence_pairs = file.read().decode('utf-8').splitlines()

            for pair in sentence_pairs:
                sentences = pair.strip().split('\t')
                if len(sentences) >= 2:
                    sentence1 = sentences[0].replace("'", "''")
                    sentence2 = sentences[1].replace("'", "''")
                    add_data = Data(sentence1, sentence2)
                    db.session.add(add_data)
            db.session.commit()
            flash("File Uploaded Successfully", "success")
            return redirect(url_for('Index'))
        else:
            flash("Invalid file format. Only .txt files are allowed.", "danger")
    return redirect(url_for('Index'))

if __name__ == '__main__':
    app.run(debug=True)