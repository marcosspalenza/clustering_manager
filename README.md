# Clustering-Manager

A basic GUI for local clustering task management. Using the [clustering optimization](https://github.com/marcosspalenza/clustering_optimization) platform for easily parameter selection, progress tracking, and delivering results. The user-interface generate the demand queue and the manager read the tasks and control the data clustering by demand.

## Requirements
- [Apache](https://www.apache.org/)
- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Waitress](https://pypi.org/project/waitress/) WSGI

## Install
Configure environment variables, install the clustering algoritm, generate the flask server, and set the linux service:

### APP.CONFIG
Initial parameters header configurations.
- Create the input path and set the clustering input location.
	Receives the user data and parameters:
	File **app.py** : `app.config['UPLOAD_LOCATION'] = "/var/www/html/clustering/input/"`
	File **control_clstropt.py** : `LOCATION_QUEUE = "/var/www/html/clustering/"`
- Set queue location:
	File **app.py** : `app.config['CTRL_LOCATION'] = "/var/www/html/clustering/"`
	File **control_clstropt.py** : `LOCATION_QUEUE = "/var/www/html/clustering/""`
- Create the input path and set the clustering output location. 
	Return the cluster information, including the cluster ids and report:
	File **app.py** : `app.config['DOWNLOAD_LOCATION'] = "/var/www/html/clustering/output/"`
	File **control_clstropt.py** : `"/var/www/html/clustering/output/"`
	Set IP access on output public folder.
	File **app.py** : `app.config['WEB_ENV'] = "http://"+HOST_IP+"/clustering/output/"`
- Python prefix called for clustering:
	File **control_clstropt.py** : `PYTHON_MODE = "python3"`
- Process identifier for Cron check:
	File **control_clstropt.py** : `PIDFILE = "/tmp/control_clstropt.pid"`
- The [clustering optimization](https://github.com/marcosspalenza/clustering_optimization) absolute path:
	File **control_clstropt.py** : `CLSTR_APP = "/home/USER/clustering/main_clustering.py"`

### Clustering 
Install the [clustering optimization](https://github.com/marcosspalenza/clustering_optimization) at the *control_clstropt.py* absolute path. Insert the file *control_clstropt.py* inside these path.

## Server
Install Flask and Waitress. Configure *app.py* settings on *serve()* function at *app.py*.

## Generate a linux service
Create */etc/init/clstropt* replace */path/to/* for *app.py* location:
># clstropt.conf
>start on filesystem
>exec python3 /path/to/app.py

Create /etc/init.d/clstropt file
># clstropt.conf
>start on filesystem
>exec python3 /path/to/app.py

Control GUI activity using:
`sudo service clstropt start`
`sudo service clstropt stop`

## Cron
Set time **crontab** cycles to execute the manager. The process remove overlap in a built-in function using **ps** command.
`10 * * * * python3 /path/to/control_clstropt.py > /path/to/error.log`