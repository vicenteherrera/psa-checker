import yaml
import os
import sys
from pathlib import Path
from datetime import datetime

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

psa_version = "0.0.1a"
chart_levels_filename = r'./result/charts_levels.md'
charts_source_filename = r'./result/helm_charts.yaml'
charts_pss_filename = r'./result/helm_charts_pss.yaml'
temp_filename = r'./result/temp.yaml'
logs_dir = r'./result/logs'
psa_checker_path = "../../release/psa-checker"

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
now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
keys_pss = charts_pss.keys()

for dic_chart in charts_source:
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart       = get_chart_name( dic_chart["url"] )
    key         = repo + "__" + chart

    i+=1
    print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + "/" + chart + " "+ version)

    if key in keys_pss:
        print("chart+repo exists on charts PSS file")
        # print(charts_pss[key]["pss"]["chart_version"])
        if charts_pss[key]["pss"]["chart_version"] == version and \
            charts_pss[key]["pss"]["psa-checker_version"] == psa_version:
            print("Skipping version already evaluated")
            continue

    log_helm       = logs_dir + "/" + repo + "_" + chart + "_" + version + "_helm.log"
    log_baseline   = logs_dir + "/" + repo + "_" + chart + "_" + version + "_baseline.log"
    log_restricted = logs_dir + "/" + repo + "_" + chart + "_" + version + "_restricted.log"
    template       = logs_dir + "/" + repo + "_" + chart + "_" + version + "_template.yaml"
    log = ""
    repo_update = 0
    gen_template = 0
    n_evaluated=0
    n_non_evaluable=0
    n_wrong_version=0
    n_crd=0

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
        "n_wrong_version":n_wrong_version
    }

    dic_chart["pss"] = psa_dict
    charts_pss[key] = dic_chart

    j+=1
    if j % 100 == 0 or i==len(dic_chart):
        print ("# Saving whole yaml")
        with open(charts_pss_filename, 'w') as file:
            yaml.dump(charts_pss, file)
    # sys.exit()

print ("# Saving whole yaml")
with open(charts_pss_filename, 'w') as file:
    yaml.dump(charts_pss, file)
