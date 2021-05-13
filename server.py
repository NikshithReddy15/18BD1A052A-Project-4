from flask import Flask, render_template, redirect, url_for, request
from flask_pymongo import PyMongo
from flask_mail import Mail, Message
import requests, dload, random, string, qrcode, os, pdfkit

import cv2 as cv2
import numpy as np
from pyzbar.pyzbar import decode

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = '18bd1a052a@gmail.com'
app.config['MAIL_PASSWORD'] = 'Chikku15'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/e-pass")
db = mongodb_client.db

@app.route('/')
def registration_form():
   return render_template('HomePage.html')

@app.route('/register',methods = ['POST', 'GET'])
def input_registration_details():
    if request.method == 'POST':
        dict1 = {'Andaman and Nicobar Islands' : 'AN', 'Andhra Pradesh' : 'AP', 'Arunachal Pradesh' : 'AR', 'Assam' : 'AS', 'Bihar' : 'BR', 'Chandigarh (UT)' : 'CH', 'Chhattisgarh' : 'CT' , 'Dadra and Nagar Haveli (UT)' : 'DN', 'Daman and Diu (UT)' : 'DN', 'Delhi (NCT)' : 'DL', 'Goa' : 'GA', 'Gujarat' : 'GJ', 'Haryana' : 'HR', 'Himachal Pradesh' : 'HP', 'Jammu and Kashmir' : 'JK', 'Jharkhand' : 'JH', 'Karnataka' : 'KA', 'Kerala' : 'KL', 'Ladakh' : 'LD', 'Lakshadweep (UT)' : 'LD', 'Madhya Pradesh' : 'MP', 'Maharashtra' : 'MH', 'Manipur' : 'MN', 'Meghalaya' : 'ML', 'Mizoram' : 'MZ', 'Nagaland' : 'NL', 'Odisha' : 'OR', 'Puducherry (UT)' : 'PY', 'Punjab' : 'PB', 'Rajasthan' : 'RJ', 'Sikkim' : 'SK', 'Tamil Nadu' : 'TN', 'Telangana' : 'TG', 'Tripura' : 'TR', 'Uttarakhand' : 'UT', 'Uttar Pradesh' : 'UP', 'West Bengal' : 'WB'}
        firstname = request.form['firstname']
        middlename = request.form['middlename']
        lastname = request.form['lastname']
        phone = request.form['phone']
        email = request.form['email']
        aadhar = request.form['aadhar']
        srcstate = request.form['source-state']
        srcdist = request.form['source-district']
        deststate = request.form['destination-state']
        temp1 = dict1[deststate]
        destdist = request.form['destination-district']
        date = request.form['date']
        data = dload.json("https://api.covid19india.org/v4/data.json")
        confirmed = data[temp1]['districts'][destdist]['total']['confirmed']
        recovered = data[temp1]['districts'][destdist]['total']['recovered']
        ratio = (recovered/confirmed)
        print("Confirmed = ", confirmed)
        print("Recovered = ", recovered)
        print("Ratio = ", ratio)
        if(ratio > 0.3):
            id1 = ''.join((random.choice(string.ascii_letters+string.digits) for x in range(20)))
            db.token.insert_one({'_id' : id1, 'name' : firstname + " " + middlename + " " + lastname, 'phone number' : phone, 'email' : email, 'aadhar' : aadhar, 'source state' : srcstate, 'source district' : srcdist, 'destination state' : deststate, 'destination district' : destdist, 'date' : date})
            qrcode.make(id1).save("C:/Users/niksh/OneDrive/Documents/FS Micro Project/Project - 4 e-Pass/static/images/"+id1+".png")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], id1+'.png')
            
            x =  render_template('approved.html', qrcode=filepath, id=id1, name=firstname + " " + middlename + " " + lastname, phone=phone, email=email, src=srcdist+", "+srcstate, dest=destdist+", "+deststate, date=date)
            options = {"enable-local-file-access": None}#, "load-error-handling": "ignore", "load-media-error-handling": "ignore"}
            pdfkit.from_string(x, 'static/pdfs/temp.pdf', options = options)
            msg = Message('e-pass Registration', sender = '18bd1a052a@gmail.com', recipients = [email])
            msg.body = "e-Pass registration"
            with app.open_resource("static/pdfs/temp.pdf") as fp:
                msg.attach("temp.pdf", "application/pdf", fp.read())
            with app.open_resource("static/images/"+id1+".png") as fp:
                msg.attach("QR.png", "images/png", fp.read())
            mail.send(msg)
            return render_template('approved.html', qrcode=filepath, id=id1, name=firstname + " " + middlename + " " + lastname, phone=phone, email=email, src=srcdist+", "+srcstate, dest=destdist+", "+deststate, date=date)
        else:
            return render_template('rejected.html', region=destdist+", "+deststate)

@app.route('/verify')
def verify():
    return render_template('/verify.html')

@app.route('/textverify', methods=['POST', 'GET'])
def textverify():
    if request.method == 'POST':
        id1 = request.form['id']
        data = db.token.find_one(id1)
        if(data):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['_id']+'.png')
            return render_template('/approved.html', qrcode=filepath, id=id1, name=data['name'], phone=data['phone number'], email=data['email'], src=data['source district']+", "+data['source state'], dest=data['destination district']+", "+data['destination state'], date=data['date'])
        else:
            return render_template('/errorverifying.html', id=id1)

@app.route('/scantoverify')
def scantoverify():
    camera = cv2.VideoCapture(0)
    data = ""
    flag = False
    while(True):
        ret, frame = camera.read()
        for bcode in decode(frame):
            data = bcode.data.decode('utf-8')
            pts = np.array([bcode.polygon], np.int32)
            cv2.polylines(frame, [pts], True, (255, 0, 0), 5)
            pts = bcode.rect
            cv2.putText(frame, data, (pts[0], pts[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (255, 0, 0), 1)
            if(data != None):
                flag = True
        cv2.imshow('Reader -- Enter a to exit', frame)
        if cv2.waitKey(1) & 0xFF == ord('a'):
            break
        if cv2.waitKey(1) & flag == True:
            break
    
    camera.release()
    cv2.destroyAllWindows()
    x = db.token.find_one(data)
    if flag == True and x != None:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], x['_id']+'.png')
        return render_template('/approved.html', qrcode=filepath, id=data, name=x['name'], phone=x['phone number'], email=x['email'], src=x['source district']+", "+x['source state'], dest=x['destination district']+", "+x['destination state'], date=x['date'])
    else:
        return render_template('/errorverifying.html', id=data)


if __name__ == '__main__':
   app.run(debug = True)