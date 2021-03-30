import os
# import secrets # Python 3.6+
import datetime
from waitress import serve
from collections import defaultdict
from werkzeug.utils import secure_filename
from flask import Flask, session, flash, render_template, request, url_for, redirect


app = Flask(__name__)

ALLOWED_EXTENSIONS = {"mat", "mtx"}
HOST_IP = "0.0.0.0"

app = Flask(__name__)
app.config['UPLOAD_LOCATION'] = "/var/www/html/clustering/input/"
app.config['DOWNLOAD_LOCATION'] = "/var/www/html/clustering/output/"
app.config['CTRL_LOCATION'] = "/var/www/html/clustering/"
app.config['WEB_ENV'] = "http://"+HOST_IP+"/clustering/output/"
# app.config["SECRET_KEY"] = secrets.token_urlsafe(16) # Add using Python 3.6+
app.config["SECRET_KEY"] = os.urandom(32) # Using Python3.5
app.permanent_session_lifetime = datetime.timedelta(days=120)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_queue(dataset):
    try:
        with open(app.config['CTRL_LOCATION']+"ctrl_queue", "a") as lock_file:
            lock_file.write(dataset+"\n")
    except:
        return False
    else:
        return True

def save_pssinfo(parameters):
    clstr_args = []
    clstr_args.append(parameters["pathin"])
    clstr_args.append("usuario="+parameters["email"])
    clstr_args.append("dataset="+parameters["dataset"])
    clstr_args.append("extension="+parameters["ext"])
    clstr_args.append("model="+parameters["mod"])
    clstr_args.append("algorithm="+parameters["algorithm"])
    clstr_args.append("metric="+parameters["metric"])
    clstr_args.append("optimizer="+parameters["optimizer"])
    clstr_args.append("index="+parameters["ivi"])
    with open (parameters["pathin"]+"parameters.cfg","w") as wtr:
        wtr.write("\n".join(clstr_args))

def check_status(dataset, user):
    queue_info = []
    try:
        with open(app.config['CTRL_LOCATION']+"ctrl_queue", "r") as lock_file:
            queue_info = [task for task in lock_file.read().split("\n") if task != ""]

        cluster_file = app.config['DOWNLOAD_LOCATION']+user+dataset+"/clusters.txt"
        exec_file = app.config['DOWNLOAD_LOCATION']+user+dataset+"/exec.csv"
        output_path = app.config['DOWNLOAD_LOCATION']+user+dataset
        if os.path.isdir(output_path):
            if os.path.isfile(exec_file) and os.path.isfile(cluster_file):
                return "success"
            else:
                return "warning"
        elif user+dataset in [qu.split(".")[0] for qu in queue_info]:
            return "info"
        else:
            return "danger"
    except Exception as e:
        print(e)
        return "danger"

def get_clusters(dataset, user):
    location = app.config['DOWNLOAD_LOCATION']+"/"+user+dataset
    clusters = []
    if os.path.isdir(location):
        with open(location+"/clusters.txt", "r") as clfile:
            clusters = [int(c) for c in clfile.read().split(" ") if c != ""]
    return clusters


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/", methods = ["GET", "POST"])
def upload_file():
   if request.method == "POST":
        if "file" not in request.files:
            print("[FILE] Not found!")
        else:
            f = request.files["file"]
            filename = secure_filename(f.filename)
            if f and allowed_file(filename):
                session["email"] = request.form["email"].lower()

                session["usuario"] = request.form["email"].lower().replace('.','').split('@')[0]

                session["dataset"] = filename.rsplit('.', 1)[0].lower()

                session["metric"] = request.form["mtr"].lower()

                session["optimizer"] = request.form["opt"].lower()

                session["algorithm"] = request.form["alg"].lower()

                session["ivi"] = request.form["idx"].lower()
                
                session["ext"] = filename.rsplit('.', 1)[1].lower()

                session["mod"] = request.form["mod"].lower()

                location = session["usuario"]+session["dataset"]

                session["pathin"] = app.config['UPLOAD_LOCATION']+session["usuario"]+session["dataset"]+"/"
                session["pathout"] = app.config['DOWNLOAD_LOCATION']+session["usuario"]+session["dataset"]+"/"


                if not os.path.isdir(session["pathin"]):
                    os.mkdir(session["pathin"])

                '''
                Fix dataset model and matrix shape divergence
                '''
                if session["mod"] == "sparse":
                    session["ext"] = "mtx"
                    f.save(os.path.join(session["pathin"], "data.mtx"))
                elif session["mod"] == "dense":
                    session["ext"] = "mat"
                    f.save(os.path.join(session["pathin"], "data.mat"))
                else:
                    f.save(os.path.join(session["pathin"], "data."+session["ext"]))

                process_flag = add_queue(location)

                if process_flag:
                    session["status"] = "info"
                    save_pssinfo(session)
                    return redirect(url_for('dataset'))
                else:
                    print("Queue unavaliable!")
            else:
                print("File extension "+filename+"not allowed!")
        return render_template("index.html")


def read_params(pathin, pss):
    cfg = []
    with open(pathin+pss+"/parameters.cfg", "r") as cfg:
        parameters = cfg.read().split("\n")         
        cfg = defaultdict()
        for p in parameters[1:]:
            if p != []:
                cfg[p.split("=")[0]] = p.split("=")[1]
    return cfg

@app.route("/search")
def search():
    dbf = [p for p in os.listdir(app.config['UPLOAD_LOCATION']) if os.path.isdir(app.config['UPLOAD_LOCATION']+p)]
    return render_template('search.html', dbfolders=dbf)

@app.route("/search", methods = ["GET", "POST"])
def select_search():
    if request.form["database"] == None:
        return render_template('search.html')
    else:
        try:
            dbloc = request.form["database"].lower()
            print(dbloc)
            if dbloc == None:
                return render_template('search.html')   
            else:
                parameters = read_params(app.config['UPLOAD_LOCATION'], dbloc)
                session["pathout"] = dbloc
                session["email"] = parameters["usuario"]
                session["usuario"] = parameters["usuario"].lower().replace('.','').split('@')[0]
                session["dataset"] = parameters["dataset"]
                session["ext"] = parameters["extension"]
                session["mod"] = parameters["model"]
                session["algorithm"] = parameters["algorithm"]
                session["metric"] = parameters["metric"]
                session["optimizer"] = parameters["optimizer"]
                session["ivi"] = parameters["index"]

                session["pathout"] = app.config['DOWNLOAD_LOCATION']+session["usuario"]+session["dataset"]+"/"
                session["status"] = check_status(session["dataset"], session["usuario"])
        except Exception as e:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M:%S")
            with open(app.config['CTRL_LOCATION']+"/app-error.log", "w") as out:
                out.write(str(current_time)+" : "+str(e)+" : "+str(session)+"\n")
        else:
            return redirect(url_for('dataset'))

    return redirect(url_for('index'))

@app.route("/dataset")
@app.route("/dataset", methods = ["GET", "POST"])
def dataset():
    try:
        print(session)
        settings = dataset_loc()
        return render_template("dataset.html", clusters=settings["clusters"], cluster_size=settings["cluster_size"],
                                cluster_path=settings["cluster_path"], cluster_exec=settings["cluster_exec"], time=settings["timer"], 
                                ss=settings["ss"], nmi=settings["nmi"], ari=settings["ari"], 
                                sse=settings["sse"], ca=settings["ca"], dbs=settings["dbs"], chs=settings["chs"]
                            )
    except Exception as e:
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        with open(app.config['CTRL_LOCATION']+"/app-error.log", "w") as out:
            out.write(str(current_time)+" : "+str(e)+" : "+str(session)+"\n")
    else:
        return redirect(url_for('dataset'))

def dataset_loc():
    if session.get('dataset') is not None:
        clsresults = defaultdict()
        session["status"] = check_status(session["dataset"], session["usuario"])
        clsresults["clusters"] = []
        clsresults["cluster_size"] = []
        clsresults["cluster_exec"] = ""
        clsresults["cluster_path"] = ""
        clsresults["timer"] = 0
        clsresults["ss"] = -1
        clsresults["sse"] = -1
        clsresults["nmi"] = -1
        clsresults["ari"] = -1
        clsresults["ca"] = -1
        clsresults["dbs"] = -1
        clsresults["chs"] = -1
        if session["status"] == "success":
            output = ""
            with open(app.config['DOWNLOAD_LOCATION']+session["usuario"]+session["dataset"]+"/exec.csv", "r") as csvout:
                output = [i for i in csvout.read().split("\n") if i != ""][-1]
            clsresults["clusters"] = get_clusters(session["dataset"], session["usuario"])
            """
            Clustering Ouput 
            0-"Dataset", 1-"Time(min)", 2-"Distance", 3-"Algorithm",
            4-"Index", 5-"Optimizer", 6-"SS", 7-"DBS", 8-"CHS", 9-"SSE",
            10-"NMI", 11-"ARI", 12-"CA", 13-"Tests", 14-"Clusters"
            ]
            """
            clsresults["timer"] = round(float(output.split("\t")[1]), 4)
            clsresults["ss"] = output.split("\t")[6]
            clsresults["dbs"] = output.split("\t")[7]
            clsresults["chs"] = output.split("\t")[8]
            clsresults["sse"] = output.split("\t")[9]
            clsresults["nmi"] = output.split("\t")[10]
            clsresults["ari"] = output.split("\t")[11]
            clsresults["ca"] = output.split("\t")[12]
            clsresults["cluster_path"] = app.config["WEB_ENV"]+session["usuario"]+session["dataset"]+"/clusters.txt"
            clsresults["cluster_exec"] = app.config["WEB_ENV"]+session["usuario"]+session["dataset"]+"/exec.csv"
            clsresults["clusters"] = " : ".join(sorted([str(len([c1 for c1 in clsresults["clusters"] if c1 == c2])) for c2 in [c for c in list(set(clsresults["clusters"]))]]))
            clsresults["cluster_size"] = len(clsresults["clusters"].split(":"))
        elif session["status"] == "warning":
            clsresults["cluster_path"] = app.config["WEB_ENV"]+session["usuario"]+session["dataset"]+"/exceptions.csv"
        return clsresults
    else:
        return render_template("index.html")

if __name__ == "__main__":
    # app.run(debug=True)
    serve(app, host="0.0.0.0", port="8888")