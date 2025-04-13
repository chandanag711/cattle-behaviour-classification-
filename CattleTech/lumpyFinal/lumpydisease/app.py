from flask import Flask, render_template, url_for, request, redirect, jsonify, session
import sqlite3
import shutil
import os
import sys
import cv2  # working with, mainly resizing, images
from grpc import Status
import numpy as np  # dealing with arrays
import os  # dealing with directories
from random import shuffle  # mixing up or currently ordered data that might lead our network astray in training.
from tqdm import \
    tqdm  # a nice pretty percentage bar for tasks. Thanks to viewer Daniel BA1/4hler for this suggestion
import tflearn
from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.estimator import regression
import tensorflow as tf
import telepot
from datetime import date
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
import csv
import threading

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
cursor.execute(command)

def analyse(image):
    IMG_SIZE = 50
    LR = 1e-3
    MODEL_NAME = 'lumpy-{}-{}.model'.format(LR, '2conv-basic')

    def process_verify_data():
        verifying_data = []
        path = 'static/test/'+image
        img_num = image.split('.')[0]
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        verifying_data.append([np.array(img), img_num])
        np.save('verify_data.npy', verifying_data)
        return verifying_data

    verify_data = process_verify_data()
    #verify_data = np.load('verify_data.npy')

    
    tf.compat.v1.reset_default_graph()
    #tf.reset_default_graph()

    convnet = input_data(shape=[None, IMG_SIZE, IMG_SIZE, 3], name='input')

    convnet = conv_2d(convnet, 32, 3, activation='relu')
    convnet = max_pool_2d(convnet, 3)

    convnet = conv_2d(convnet, 64, 3, activation='relu')
    convnet = max_pool_2d(convnet, 3)

    convnet = conv_2d(convnet, 128, 3, activation='relu')
    convnet = max_pool_2d(convnet, 3)

    convnet = conv_2d(convnet, 32, 3, activation='relu')
    convnet = max_pool_2d(convnet, 3)

    convnet = conv_2d(convnet, 64, 3, activation='relu')
    convnet = max_pool_2d(convnet, 3)

    convnet = fully_connected(convnet, 1024, activation='relu')
    convnet = dropout(convnet, 0.8)

    convnet = fully_connected(convnet, 2, activation='softmax')
    convnet = regression(convnet, optimizer='adam', learning_rate=LR, loss='categorical_crossentropy', name='targets')

    model = tflearn.DNN(convnet, tensorboard_dir='log')

    if os.path.exists('{}.meta'.format(MODEL_NAME)):
        model.load(MODEL_NAME)
        print('model loaded!')


    # fig = plt.figure()
    diseasename=" "
    rem=" "
    rem1=" "
    str_label=" "
    for num, data in enumerate(verify_data):

        img_num = data[1]
        img_data = data[0]

        # y = fig.add_subplot(3, 4, num + 1)
        orig = img_data
        data = img_data.reshape(IMG_SIZE, IMG_SIZE, 3)
        # model_out = model.predict([data])[0]
        model_out = model.predict([data])[0]
        print(model_out)
        print('model {}'.format(np.argmax(model_out)))

        if np.argmax(model_out) == 0:
            str_label = 'lumpy'
            print("The predicted image islumpy is with a accuracy of {} %".format(model_out[0]*100))
            accuracy = "The predicted image is lumpy is with a accuracy of {} %".format(model_out[0]*100)
        
        elif np.argmax(model_out) == 1:
            str_label = 'healthy'
            print("The predicted image is healthy is with a accuracy of {} %".format(model_out[1]*100))
            accuracy = "The predicted image is healthy is with a accuracy of {} %".format(model_out[1]*100)

        return str_label, accuracy

import os 

app = Flask(__name__)
app.secret_key =  os.urandom(12)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tracking')
def tracking():
    return render_template('tracking.html')

@app.route('/userlog', methods=['GET', 'POST'])
def userlog():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']

        query = "SELECT name, password FROM user WHERE name = '"+name+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result:
            session['user'] = result[0]
            connection = sqlite3.connect(str(session['user'])+'.db')
            cursor = connection.cursor()
            cursor.execute('create table if not exists cattle(Id TEXT, Date TEXT)')
            cursor.execute('create table if not exists Tracking(Id TEXT, Exit TEXT, Entry TEXT)')
            return render_template('userlog.html', name = session['user'].lower())
        else:
            return render_template('index.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('index.html')


@app.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mobile = request.form['phone']
        email = request.form['email']
        
        print(name, mobile, email, password)

        cursor.execute("select * from user where name = '"+name+"' or email = '"+email+"'")
        result = cursor.fetchone()
        if result:
            return render_template('index.html', msg='username or email already exists')
        else:
            cursor.execute("INSERT INTO user VALUES ('"+name+"', '"+password+"', '"+mobile+"', '"+email+"')")
            connection.commit()

            return render_template('index.html', msg='Successfully Registered')
    
    return render_template('index.html')

@app.route('/lumpy_disease', methods=['GET', 'POST'])
def lumpy_disease():
    if request.method == 'POST':
        image = request.form['img']
        str_label, accuracy = analyse(image)
        return render_template('userlog.html',name = session['user'].lower(), status=str_label, accuracy=accuracy, ImageDisplay="http://127.0.0.1:5000/static/test/"+image)
    return render_template('userlog.html', name = session['user'].lower())

@app.route('/view_cattle')
def view_cattle():
    connection = sqlite3.connect(str(session['user'])+'.db')
    cursor = connection.cursor()

    cursor.execute("select * from cattle")
    result = cursor.fetchall()

    print(result)
    return render_template('add_data.html',name = session['user'].lower(), result=result)

@app.route('/track_cattle')
def track_cattle():
    connection = sqlite3.connect(str(session['user'])+'.db')
    cursor = connection.cursor()

    cursor.execute("select * from Tracking")
    result = cursor.fetchall()

    print(result)
    return render_template('tracking.html',name = session['user'].lower(), result=result)

@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if request.method == 'POST':

        connection = sqlite3.connect(str(session['user'])+'.db')
        cursor = connection.cursor()

        
        Id = request.form['id']
        date1 = request.form['date1']
        data = [Id, date1]
        print(data)
        cursor.execute('insert into cattle values(?, ?)', data)
        connection.commit()

        return redirect(url_for('view_cattle'))
    return redirect(url_for('view_cattle'))

@app.route('/Update', methods=['GET', 'POST'])
def Update():
    if request.method == 'POST':

        connection = sqlite3.connect(str(session['user'])+'.db')
        cursor = connection.cursor()

        
        Id = request.form['id']
        date1 = request.form['date1']
        data = [Id, date1]
        print(data)
        cursor.execute("update cattle set Date = '"+date1+"' where Id = '"+str(Id)+"'")
        connection.commit()

        return redirect(url_for('view_cattle'))
    return redirect(url_for('view_cattle'))

@app.route('/Exit')
def Exit():
    connection = sqlite3.connect(str(session['user'])+'.db')
    cursor =connection.cursor()
    from test import Tracking
    Id = Tracking()

    from datetime import datetime
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    print("date and time:",date_time)
    cursor.execute("insert into Tracking (Id, Exit) values (?,?)", [Id, date_time])
    connection.commit()
    return redirect(url_for('track_cattle'))

@app.route('/Entry')
def Entry():
    connection = sqlite3.connect(str(session['user'])+'.db')
    cursor =connection.cursor()
    from test import Tracking
    Id = Tracking()

    from datetime import datetime
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
    print("date and time:",date_time)
    cursor.execute("Update Tracking set Entry = ? where Id = ?", [date_time, Id])
    connection.commit()
    return redirect(url_for('track_cattle'))

@app.route('/Delete/<Id>')
def Delete(Id):
    print('id is', Id)
    connection = sqlite3.connect(str(session['user'])+'.db')
    cursor =connection.cursor()
    query = "delete from cattle where Id = '"+str(Id)+"'"
    cursor.execute(query)
    connection.commit()
    return redirect(url_for('view_cattle'))


@app.route('/get_data')
def get_data():
    con = sqlite3.connect(str(session['user'])+'.db')
    cr = con.cursor()

    cr.execute('select * from cattle')
    result = cr.fetchall()
    print(result)
    if result:
        today = date.today()
        today = pd.to_datetime(today)

        posts = []
        for row in result:
        
            end = pd.to_datetime(row[1])
            if (today - end).days == -1:
                msg="Vaccination required for cow id {} on tommorrow".format(row[0])
                print(msg)
                posts.append(msg)
                bot = telepot.Bot("8161329839:AAG4Vyr7B0riWQap5claQMqtL52CpyqJIBw")
                bot.sendMessage("5587918950", str(msg))
                bot = telepot.Bot("7792718299:AAFSvfcPGpBWCFJx-BddAqo7DCFFVylTUlI")
                bot.sendMessage("1967259059", str(msg))
                bot = telepot.Bot("7173027390:AAGtrjBgTKzadlpGBjJbkVO8qw_y9F6y_Ng")
                bot.sendMessage("2043356316", str(msg))
                bot = telepot.Bot("7336448383:AAG9biC3i8SCf86IJEjMRpwLdpmyZgzRffQ")
                bot.sendMessage("1040058032", str(msg))

        return jsonify(posts)
    else:
        return jsonify(['data not found'])

@app.route('/market')
def  market():
    url = "https://www.napanta.com/market-price/karnataka/bangalore/bangalore"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table with class "table table-bordered table-striped"
    table = soup.find("table")
    if table:
        result =[['Commodity', 'Variety', 'Maximum Price',	'Average Price', 'Minimum Price', 'Last Updated On']]
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if cells:
                d = [cell.get_text(strip=True) for cell in cells]
                result.append(d[:-1])
        return render_template('market.html',name = session['user'].lower(), result=result)
    else:
        return render_template('home.html',name = session['user'].lower())
    
        
@app.route('/reminder')
def reminder():
    return render_template('reminder.html', name = session['user'].lower())

@app.route('/profile')
def profile():
    con = sqlite3.connect(str(session['user'])+'.db')
    cr = con.cursor()
    cr.execute('select * from cattle')
    no_cow = cr.fetchall()

    connection = sqlite3.connect('user_data.db')
    cursor = connection.cursor()

    query = "SELECT mobile, email FROM user WHERE name = '"+str(session['user'])+"'"
    cursor.execute(query)
    result = cursor.fetchone()
    phone = result[0]
    email = result[1]
    return render_template('profile.html', name = session['user'].lower(), no_cow=len(no_cow), phone=phone, email=email)

@app.route('/logout')
def logout():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
