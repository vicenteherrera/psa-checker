import yaml
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time
from datetime import timedelta

def get_chart_name(url):
    parts = url.split("/")
    user  = parts[ len(parts) - 1 ]
    return user

def is_in_file(str, filename):
    with open(filename, 'r') as fp:
        for l_no, line in enumerate(fp):
            if str in line:
                return True
    return False

def count_in_file(str, filename):
    n=0
    with open(filename, 'r') as fp:
        for l_no, line in enumerate(fp):
            if str in line:
                n += 1
    return n

def evaluate_badrobot(template, log_badrobot):
    os.system("badrobot scan " + template + " | jq '[.[].score] | add' > " + log_badrobot)
    with open(log_badrobot) as f:
        score_badrobot = f.readline().strip('\n')
    return score_badrobot

start = datetime.now()
psa_version = "0.0.1"
chart_levels_filename = r'./result/charts_levels.md'
charts_source_filename = r'./result/helm_charts.yaml'
charts_pss_filename = r'./result/helm_charts_pss.yaml'
temp_filename = r'./result/temp.yaml'
logs_dir = r'./result/logs'
psa_checker_path = "../../release/psa-checker"

psa_version = subprocess.getoutput(psa_checker_path + ' --version')
psa_version = psa_version[len("psa-checker version "):]
print("# psa-checker version "+ psa_version)

print("# Reading charts list files")

print("  1. reading AH source file ")
file = open(charts_source_filename, 'r')
charts_source = yaml.safe_load(file)
file.close()

if os.path.exists(charts_pss_filename):
    print("  2. reading existing charts PSS")
    
    file = open(charts_pss_filename, 'r')
    charts_pss = yaml.safe_load(file)
    file.close()
else:
    print("  2. charts PSS not found, creating new one")
    charts_pss = {}

# TODO: Remove evaluated charts that no longer appear in Artifact Hub

print("# Iterating charts")
i=0
j=0
evaluated=[]
now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
keys_pss = charts_pss.keys()

for dic_chart in charts_source:
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart       = get_chart_name( dic_chart["url"] )
    logs_prefix = logs_dir + "/" + repo + "_" + chart + "_" + version
    log_badrobot = logs_prefix + "_badrobot.log"
    template     = logs_prefix + "_template.yaml"
    key         = repo + "__" + chart
    
    i+=1
    print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + "/" + chart + " "+ version)

    if key in keys_pss:
        print("  Chart+repo exists on charts PSS file")
        if not "score_badrobot" in charts_pss[key]["pss"]:
            if charts_pss[key]["pss"]["level"][0:5]=="error":
                print("    Skipping badrobot score for chart in state: " + charts_pss[key]["pss"]["level"])
            else:
                print("  Adding badrobot evaluation")
                charts_pss[key]["pss"]["score_badrobot"] = evaluate_badrobot(template, log_badrobot)
                print("    Badrobot score: " + charts_pss[key]["pss"]["score_badrobot"])
                j += 1
        else:
            print("    Skipping badrobot score already evaluated: " + charts_pss[key]["pss"]["score_badrobot"])
        if charts_pss[key]["pss"]["psa-checker_version"] == psa_version:
            if charts_pss[key]["pss"]["chart_version"] == version:
                print("    Skipping chart version " + version + " already evaluated with psa-checker " + psa_version)
                continue
            if charts_pss[key]["pss"]["chart_version"] > version:
                print("    Skipping chart version " + version + " is lower than " + charts_pss[key]["pss"]["chart_version"] + " already evaluated with psa-checker " + psa_version)
                continue

    log_helm       = logs_prefix + "_helm.log"
    log_baseline   = logs_prefix + "_baseline.log"
    log_restricted = logs_prefix + "_restricted.log"
    log = ""
    repo_update = 0
    gen_template = 0
    n_evaluated=0
    n_non_evaluable=0
    n_wrong_version=0
    n_crd=0
    score_badrobot=""

    if not os.path.exists(log_helm):
        print("  Downloading chart")
        os.system("helm repo add " + repo + " " + url + " 1>" + log_helm + " 2>&1")
        repo_update = os.system("helm repo update " + repo + " 1>>" + log_helm + " 2>&1")
    
    if repo_update >0 or is_in_file("cannot be reached", log_helm):
        level = "error_download"
    else:
        
        if not os.path.exists(template):
            print("  Generating template")
            gen_template = os.system("helm template " + repo + "/" + chart + " --version " + version + " >" + template + " 2>>" + log_helm)
        else:
            print("  Template cached")
        template_data = Path(template).read_text()
        if ( gen_template >0 or is_in_file("error",log_helm)):
            level = "error_template"
        else:
            if not os.path.exists(template):
                print("Error, no template generated")
                level = "error_no_template"
                log = log_helm
            else: 
                print("  PSS evaluation: baseline")
                baseline   = os.system("cat " + template + " | " + psa_checker_path + " --level baseline   -f - >" + log_baseline + " 2>&1")
                print("  PSS evaluation: restricted")
                restricted = os.system("cat " + template + " | " + psa_checker_path + " --level restricted -f - >" + log_restricted + " 2>&1")
                n_evaluated=count_in_file("PSS level",log_restricted)-1
                n_non_evaluable=count_in_file("Kind not evaluable",log_restricted)
                n_wrong_version=count_in_file("not evaluable for kind:",log_restricted)
                n_crd=count_in_file("Non standard k8s node found",log_restricted)
                print("    Objects non-evaluable: " + str(n_non_evaluable))
                print("    Objects evaluated: " + str(n_evaluated))
                print("    Objects CRD: " + str(n_crd))
                print("    Objects wrong version: " + str(n_wrong_version))
                
                if n_wrong_version > 0:
                    level = "version_not_evaluable"
                elif (n_evaluated+n_non_evaluable+n_crd) == 0:
                    level = "empty_no_object"
                elif n_evaluated == 0:
                    if n_crd==0:
                        level = "no_pod_object"
                    else:
                        level = "no_pod_object_but_crd"
                elif ( restricted == 0 and baseline == 0):
                    level = "restricted"
                elif (baseline==0):
                    level = "baseline"
                else:
                    level = "privileged"

    print("  Level: " + level)

    if level=="error":
        print("    Skipping badrobot score for chart in state: " + level)
    else:
        print("  Adding badrobot evaluation")
        score_badrobot = evaluate_badrobot(template, log_badrobot)
        print("    Badrobot score: " + score_badrobot)

    psa_dict = {
        "level" : level,
        "chart_version" : version,
        "log_restricted": log_restricted,
        "log_baseline": log_baseline,
        "date": now,
        "psa-checker_version" : psa_version,
        "n_evaluated": n_evaluated, 
        "n_non_evaluable":n_non_evaluable,
        "n_crd": n_crd,
        "n_wrong_version":n_wrong_version,
        "score_badrobot":score_badrobot
    }

    dic_chart["pss"] = psa_dict
    charts_pss[key] = dic_chart

    j+=1
    evaluated.append(key)
    if j % 100 == 0:
        print ("# Saving whole PSS yaml")
        with open(charts_pss_filename, 'w') as file:
            yaml.dump(charts_pss, file)
    # sys.exit()

print(str(j) + " new charts/version evaluated in " + str(datetime.now() - start))

# print(evaluated)
if j>0:
    print ("# End, force saving whole PSS yaml")
    with open(charts_pss_filename, 'w') as file:
        yaml.dump(charts_pss, file)

