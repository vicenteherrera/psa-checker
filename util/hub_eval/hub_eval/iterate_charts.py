import yaml
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time
from datetime import timedelta

import charts_lib


def needs_update(repo, chart, dic_chart, charts_pss):
    key = repo + "__" + chart
    version = dic_chart["version"]
    if not "status" in charts_pss[key] or charts_pss[key]["status"]["chart_version"] != version:
        return True
    return False

def needs_evaluation(repo, chart, tool, charts_pss):
    key = repo + "__" + chart
    if "status" not in charts_pss or "chart_version" not in charts_pss["status"]:
        return False
    if not "generated" in charts_pss["status"] or charts_pss["status"]["generated"] != "generated":
        return False
    if tool not in charts_pss or "chart_version" not in charts_pss[tool]:
        return True
    if charts_pss[tool]["chart_version"] != charts_pss[status]["chart_version"]:
        return True
    return False

def evaluate_pss(repo, chart
    logs_prefix    = logs_dir + "/" + repo + "_" + chart + "_" + version
    log_baseline   = logs_prefix + "_baseline.log"
    log_restricted = logs_prefix + "_restricted.log"
    template       = logs_prefix + "_template.yaml"
    key            = repo + "__" + chart
 
    log = ""
    n_evaluated=0
    n_non_evaluable=0
    n_wrong_version=0
    n_crd=0
    
    if not os.path.exists(template):
        print("Error, no template generated")
        sys.exit(1)
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
    }

    return psa_dict


# -----------------------------------------------------------------------


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


now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
keys_pss = charts_pss.keys()

print("# Downloading charts and generating templates")

i=0
j=0
for dic_chart in charts_source:
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart       = get_chart_name( dic_chart["url"] )
    logs_prefix    = logs_dir + "/" + repo + "_" + chart + "_" + version
    log_helm       = logs_prefix + "_helm.log"
    template       = logs_prefix + "_template.yaml"
    key            = repo + "__" + chart
    
    i+=1
    print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + "/" + chart + " "+ version)

    log = ""
    repo_update = 0
    gen_template = 0
    
    status="no"

    if not os.path.exists(log_helm) or needs_update(repo, chart, dic_chart, charts_pss):
        print("  Downloading chart")
        os.system("helm repo add " + repo + " " + url + " 1>" + log_helm + " 2>&1")
        repo_update = os.system("helm repo update " + repo + " 1>>" + log_helm + " 2>&1")
        # TODO: make sure latest version equals AH version

    if repo_update >0 or is_in_file("cannot be reached", log_helm):
        status = "error_download"
    else:
        status = "generated"
        if not os.path.exists(template) or needs_update(repo, chart, dic_chart, charts_pss):
            # TODO: retry previously errored templates 
            print("  Generating template")
            gen_template = os.system("helm template " + repo + "/" + chart + " --version " + version + " >" + template + " 2>>" + log_helm)
        else:
            print("  Template cached")
        template_data = Path(template).read_text()
        if ( gen_template >0 or is_in_file("error",log_helm)):
            status = "error_template"

    status = {
        "cache" : status,
        "chart_version" : version
        "datetime" : now,
    }

    charts_pss[key]["status"] = status

    j+=1
    if j % 100 == 0:
        print ("# Saving whole charts DB yaml")
        with open(charts_pss_filename, 'w') as file:
            yaml.dump(charts_pss, file)
    # sys.exit()

yaml.dump(charts_pss, file)
 
print("# Iterating charts")
i=0
j=0
evaluated=[]

for dic_chart in charts_source:
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart       = get_chart_name( dic_chart["url"] )
    logs_prefix    = logs_dir + "/" + repo + "_" + chart + "_" + version
    log_badrobot   = logs_prefix + "_badrobot.log"
    log_helm       = logs_prefix + "_helm.log"
    log_baseline   = logs_prefix + "_baseline.log"
    log_restricted = logs_prefix + "_restricted.log"
    template       = logs_prefix + "_template.yaml"
    key            = repo + "__" + chart
    
    i+=1
    print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + "/" + chart + " "+ version)

    if needs_evaluation(repo, chart, "badrobot", charts_pss):
        print("  Adding badrobot evaluation")
        charts_pss[key]["badrobot"] = {
           "score": evaluate_badrobot(template, log_badrobot),
           "date": now
        }
        print("    Badrobot score: " + charts_pss[key]["badrobot"]["score"])
        j += 1
    
    if needs_evaluation(repo, chart, "pss", charts_pss):
        print("  Adding PSS evaluation")
        charts_pss[key]["pss"] = evaluate_pss(repo, chart)
        j += 1

    charts_pss[key] = dic_chart

    # evaluated.append(key)
    
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

