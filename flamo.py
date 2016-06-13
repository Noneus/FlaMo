#!/usr/bin/env python3
'''
The MIT License (MIT)

Copyright (c) 2016 Stefan Lohmaier

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import os

import flask
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask_login import LoginManager, UserMixin
from flask_login import login_required, login_user, logout_user
from easysettings import EasySettings

from flashforge import FlashForge

'''
Setup the app and all subsytems
'''
#some default values
DEFAULT_PASSWORD = 'flamo'

#create the app
app = Flask('flamo')
app.config['SECRET_KEY'] = os.environ.get('FLAMO_SECRET_KEY', 'flamo')

#login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#socket io server
socketio = SocketIO(app)

#settings
settings = EasySettings('flamo.conf')

#printer
ff = FlashForge(autoconnect=False)

'''
Implementation
'''

#default route index route
@app.route('/', methods=['GET'])
@login_required
def index():
	return render_template('index.html', streamurl=settings.get('streamurl'))

def machine_state():
	if not ff.connected:
		ff.connect()
	
	status = ff.machine_status()
	socketio.emit('machine_state', status)

def machine_information():
	if not ff.connected:
		ff.connect()
	
	info = ff.machine_information()
	socketio.emit('machine_information', info)

'''
SocketIO callbacks
'''

@socketio.on('get_machine_state')
def socketio_machine_state():
	machine_state()

@socketio.on('get_machine_information')
def socketio_machine_information():
	machine_information()

@socketio.on('hello')
def socketio_hello():
	machine_state()
	machine_information()

'''
Authentication methods
'''
#dummy user class for flask-login
class User(UserMixin):
	def get_id(self):
		return 'user'

#function to load user for login-manager
@login_manager.user_loader
def load_user(id):
	return User()

#load user from request header
@login_manager.request_loader
def load_user_request(request):
	token = request.headers.get('Authorization')
	if token is None:
		token = request.args.get('token')
	
	if token == settings.get('password'):
		return User()
	else:
		return None

#login-view to show when not authenticated
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		request.form['password'] == settings.get('password', 'flamo')
		login_user(User())
		return flask.redirect('/')
	
	return render_template('login.html')

#route to logout
@app.route('/logout')
@login_required
def logout():
	logout_user()
	flask.redirect('/login')

'''
main-function? run devserver
'''
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', debug=True)
