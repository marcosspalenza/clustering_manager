import os
import subprocess
from time import sleep
from collections import defaultdict

PIDFILE = "/tmp/control_clstropt.pid"
PYTHON_MODE = "python3"
CLSTR_APP = "/home/user/clustering/main_clustering.py"
LOCATION_QUEUE = "/var/www/html/clustering/"
LOCATION_IN = "/var/www/html/clustering/input/"
LOCATION_OUT = "/var/www/html/clustering/output/"

def is_running():
    pschk = "ps up `cat "+PIDFILE+"` >/dev/null && echo 'Wait' || echo 'Run'"
    
    output = subprocess.getoutput(pschk)

    if output.split('\n')[-1] == "Wait":
        print("[Process]"+str(PIDFILE)+" already exists.")
    else:
        pid = str(os.getpid())
        with open(PIDFILE, "w") as pidwtr:
            pidwtr.write(pid)
        return False
    return True

def read_queue(loc = "./", filename = "demand"):
    process = []
    lock_file = loc+filename
    if os.path.isfile(lock_file):
        with open(lock_file, "r") as qrd:
            process = [qitem for qitem in qrd.read().split("\n") if qitem != ""]
    return process

def update_queue(removed, loc = "./", filename = "demand"):
    process = []
    lock_file = loc+filename
    
    with open(lock_file, "r") as qrd:
        process = [qitem for qitem in qrd.read().split("\n") if qitem != ""]

    if removed == process[0]:
        with open(lock_file, "w") as qrd:
            for p in process[1:]:
                qrd.write(p+"\n")

def run_clustering(pss, cfg):
    """
    key => value
    "usuario" parameters["email"]
    "dataset" parameters["dataset"]
    "extension" parameters["ext"]
    "model" parameters["mod"]
    "algorithm" parameters["algorithm"]
    "metric" parameters["metric"]
    "optimizer" parameters["optimizer"]
    "index" parameters["ivi"]
    """
    if not os.path.isdir(LOCATION_OUT+pss+"/"):
        os.mkdir(LOCATION_OUT+pss+"/")

    if cfg == []:
        location_in = LOCATION_IN+pss+"/"
        location_out = LOCATION_OUT+pss+"/"

        dbname = [d for d in os.listdir(location_in) if ".mtx" in d or ".mat" in d][0]

        os.system(PYTHON_MODE+" "+CLSTR_APP+" -i "+location_in+" -o "+location_out+" "+dbname)

    else:
        dbfile = "data."+cfg["extension"]
        # dblbl = pss+".labels"

        folder = cfg["usuario"].replace('.','').split('@')[0]+cfg["dataset"]+"/"

        location_in = LOCATION_IN+folder
        location_out = LOCATION_OUT+folder

        if not os.path.isdir(LOCATION_OUT):
            os.mkdir(LOCATION_OUT)

        mtr = cfg["metric"]
        ivi = cfg["index"]
        alg = cfg["algorithm"]
        opt = cfg["optimizer"]

        model = cfg["model"]
        os.system(PYTHON_MODE+" "+CLSTR_APP+" -a "+alg+" -t "+opt+" -e "+ivi+" -f "+model+" -i "+location_in+" -o "+location_out+" -d "+mtr+" "+dbfile)

def read_params(pathin, pss):
    cfg = []
    with open(pathin+pss+"/parameters.cfg", "r") as cfg:
        parameters = cfg.read().split("\n")
                    
        cfg = defaultdict()
        for p in parameters[1:]:
            if p != []:
                cfg[p.split("=")[0]] = p.split("=")[1]

    return cfg

def clustering(psqueue):
    ps = psqueue[0]
    cfg = read_params(LOCATION_IN, ps)
    run_clustering(ps, cfg)
    update_queue(ps, loc=LOCATION_QUEUE, filename="ctrl_queue")
    return psqueue[1:]
    
def main():
    ps_queue = read_queue(loc=LOCATION_QUEUE, filename="ctrl_queue")
    while ps_queue != []:
        try:
            ps_queue = read_queue(loc=LOCATION_QUEUE, filename="ctrl_queue")
            print("Clustering!")
            ps_queue = clustering(ps_queue)
        except Exception as e:
            print("Err! Manager unable to execute the task")
            print(e)

if __name__ == "__main__":
    if not is_running():
        print("[Process] Running!")
        main()
        os.unlink(PIDFILE)
        print("[Process] End!")
    else:
        print("[Process] Controller already started! Wait the current process end!")
