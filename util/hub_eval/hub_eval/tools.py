import os
import sys
from datetime import datetime
import yaml
import urllib

import charts_lib
import tools

def evaluate_pss(repo, chart, version):
    psa_version = "0.0.1"
    # psa_version = subprocess.getoutput(psa_checker_path + ' --version')
    # psa_version = psa_version[len("psa-checker version "):]

    start = datetime.now()
    now = start.strftime("%Y-%m-%d, %H:%M:%S")
    logs_dir = r'./result/cache'
    logs_prefix    = logs_dir + "/" + urllib.parse.quote(repo + "_" + chart + "_" + version)
    log_baseline   = logs_prefix + "_baseline.log"
    log_restricted = logs_prefix + "_restricted.log"
    template       = logs_prefix + "_template.yaml"

    psa_checker_path = "../../release/psa-checker"

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
        n_evaluated = charts_lib.count_in_file("PSS level", log_restricted) - 1
        n_non_evaluable = charts_lib.count_in_file("Kind not evaluable", log_restricted)
        n_wrong_version = charts_lib.count_in_file("not evaluable for kind:", log_restricted)
        n_crd = charts_lib.count_in_file("Non standard k8s node found", log_restricted)
        print("    Objects non-evaluable: " + str(n_non_evaluable))
        print("    Objects evaluated: " + str(n_evaluated))
        print("    Objects CRD: " + str(n_crd))
        print("    Objects wrong version: " + str(n_wrong_version))
        
        if n_wrong_version > 0:
            level = "version_not_evaluable"
        elif ( n_evaluated+n_non_evaluable + n_crd ) == 0:
            level = "empty_no_object"
        elif n_evaluated == 0:
            if n_crd == 0:
                level = "no_pod_object"
            else:
                level = "no_pod_object_but_crd"
        elif ( restricted == 0 and baseline == 0 ):
            level = "restricted"
        elif ( baseline == 0 ):
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

# --------------------------------------------------------------------

def evaluate_badrobot(repo, chart, version):
    logs_dir = r'./result/cache'
    logs_prefix    = logs_dir + "/" + urllib.parse.quote(repo + "_" + chart + "_" + version)
    log_badrobot   = logs_prefix + "_badrobot.log"
    template       = logs_prefix + "_template.yaml"
    now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    os.system("badrobot scan " + template + " > " + log_badrobot )
    os.system("cat " + log_badrobot + " | jq '[.[].score] | add' > " + log_badrobot + "_sum")
    with open(log_badrobot+"_sum") as f:
        score_badrobot = f.readline().strip('\n')
    result = {
        "chart_version" : version,
        "score": score_badrobot,
        "date": now
    }
    return result

# --------------------------------------------------------------------

def evaluate_tool(repo, chart, version, tool):
    match tool:
        case "pss":
            return evaluate_pss(repo, chart, version)
        case "badrobot":
            return evaluate_badrobot(repo, chart, version)

# --------------------------------------------------------------------

def evaluate(charts_source, charts_pss, charts_pss_filename):
    logs_dir = r'./result/cache'
    start = datetime.now()
    now = start.strftime("%Y-%m-%d, %H:%M:%S")
    
    print("# Evaluating charts with tools")
    i=0
    j=1
    evaluated=[]

    for dic_chart in charts_source:
        repo        = dic_chart["repository"]["name"]
        version     = dic_chart["version"]
        # app_version = dic_chart["app_version"]
        chart       = charts_lib.get_chart_name( dic_chart["url"] )
        key            = repo + "__" + chart
        tools_list = ["badrobot","pss"]

        i+=1
        print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + "/" + chart + " "+ version)

        for tool in tools_list:
            if charts_lib.needs_evaluation(repo, chart, tool, charts_pss):
                print("  Adding %s evaluation" % tool)
                charts_pss[key][tool] = tools.evaluate_tool(repo, chart, version, tool)
                j += 1

        # evaluated.append(key)
        
        # if j % 10 == 0:
        #     print ("# Saving whole PSS yaml")
        #     with open(charts_pss_filename, 'w') as file:
        #         yaml.dump(charts_pss, file)
        #     break

    print( str( j - 1 ) + " charts new evaluations done in " + str( datetime.now() - start ) )

    # print(evaluated)
    
    if j>1:
        print("# End, force saving whole PSS yaml")
        with open(charts_pss_filename, 'w') as file:
            yaml.dump(charts_pss, file)
