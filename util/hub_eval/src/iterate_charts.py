import yaml
import os
import sys
from datetime import datetime

def read_n_to_last_line(filename, n = 1):
    """Returns the nth before last line of a file (n=1 gives last line)"""
    num_newlines = 0
    with open(filename, 'rb') as f:
        try:
            f.seek(-2, os.SEEK_END)    
            while num_newlines < n:
                f.seek(-2, os.SEEK_CUR)
                if f.read(1) == b'\n':
                    num_newlines += 1
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line

def get_chart_name(url):
    parts = url.split("/")
    user  = parts[ len(parts) - 1 ]
    return user

psa_version = "0.0.1"
chart_levels_filename = r'./result/charts_levels.md'
charts_source_filename = r'./result/helm_charts.yaml'
charts_pss_filename = r'./result/helm_charts_pss.yaml'
temp_filename = r'./result/temp.yaml'
logs_dir = r'./result/logs'
psa_checker_path = "../../release/psa-checker"
check_source = True

print("# Reading all charts")
if os.path.exists(charts_pss_filename):
    filename = charts_pss_filename
else:
    filename = charts_source_filename

print("1. reading "+filename)
file = open(filename, 'r')
charts = yaml.safe_load(file)
file.close()

if filename == charts_source_filename:
    check_source = False
else:
    print("2. reading "+charts_source_filename)
    file = open(charts_source_filename, 'r')
    charts_source = yaml.safe_load(file)
    file.close()

# TODO: Loop to insert new items from chart:source in charts

print("# Ordering charts alphabetically")
charts.sort(key=lambda x: x["repository"]["name"] + " " + get_chart_name( x["url"] ) )

print("# Iterating charts")
i=0
now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
for dic_chart in charts:
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart       = get_chart_name( dic_chart["url"] )
    i+=1

    if "pss" in dic_chart:
        print("PSS info present")
        if dic_chart["pss"]["chart_version"] == version:
            print("Skipping " + str(i) + " " + repo + " " +  chart + " " + version)
            continue

    print( "# ["+ str(i) + "/" + str(len(charts))+ "] " + repo + " " + chart + " " + url)
    os.system("helm repo add " + repo + " " + url)
    os.system("helm repo update " + repo)
    gen_template = os.system("helm template " + repo + "/" + chart + " --version " + version + " >" + temp_filename)

    log = ""
    if ( gen_template >0 ):
        level = "error"
    else:
        log_baseline = logs_dir + "/" + repo + "_" + chart + "_baseline.log"
        log_restricted = logs_dir + "/" + repo + "_" + chart + "_restricted.log"

        baseline   = os.system("cat " + temp_filename + " | " + psa_checker_path + " --level baseline   -f - >" + log_baseline)
        restricted = os.system("cat " + temp_filename + " | " + psa_checker_path + " --level restricted -f - >" + log_restricted)
        if ( restricted == 0 and baseline == 0):
            level = "restricted"
            log = log_restricted
        elif (baseline==0):
            level = "baseline"
            log = log_restricted
        else:
            level = "privileged"
            log = log_baseline

    print("Level: " + level)

    psa_dict = {
        "level" : level,
        "chart_version" : version,
        "log": log,
        "date": now,
        "psa-checker_version" : psa_version
    }
    dic_chart["pss"] = psa_dict

    if i % 10 == 0 or True:
        print ("# Saving whole yaml")
        with open(charts_pss_filename, 'w') as file:
            yaml.dump(charts, file)

    # sys.exit()
