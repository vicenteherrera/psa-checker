import os
from datetime import datetime
import yaml
import urllib

import charts_lib

def generate(charts_source, charts_pss, charts_pss_filename):
    logs_dir = r'./result/cache'
    now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    keys_pss = charts_pss.keys()

    # TODO: Remove evaluated charts that no longer appear in Artifact Hub

    i=0
    j=1
    for dic_chart in charts_source:
        repo        = dic_chart["repository"]["name"]
        url         = dic_chart["repository"]["url"]
        version     = dic_chart["version"]
        chart       = charts_lib.get_chart_name( dic_chart["url"] )
        logs_prefix    = logs_dir + "/" + urllib.parse.quote(repo + "_" + chart + "_" + version)
        log_helm       = logs_prefix + "_helm.log"
        template       = logs_prefix + "_template.yaml"
        key            = repo + "__" + chart
        # TODO: Make sure there is no collision with slugify names
        
        i+=1
        print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + "/" + chart + " "+ version)

        log = ""
        repo_update = 0
        gen_template = 0
        
        status="no"

        if not os.path.exists(log_helm) or charts_lib.needs_update(repo, chart, dic_chart, charts_pss):
            print("  Downloading chart")
            os.system("helm repo add " + repo + " " + urllib.parse.quote_plus(url) + " 1>" + log_helm + " 2>&1")
            repo_update = os.system("helm repo update " + repo + " 1>>" + log_helm + " 2>&1")
            # TODO: make sure latest version equals AH version

        if repo_update >0 or charts_lib.is_in_file("cannot be reached", log_helm):
            print("  **Error downloading chart")
            status = "error_download"        
        else:
            if not os.path.exists(template) or charts_lib.needs_update(repo, chart, dic_chart, charts_pss):
                # TODO: retry previously errored templates 
                print("  Generating template")
                gen_template = os.system("helm template \"" + urllib.parse.quote_plus(repo + "/" + chart) + "\" --version " + version + " >" + template + " 2>>" + log_helm)
            else:
                print("  Template cached")
            status = "generated"
            # template_data = Path(template).read_text()
            if ( gen_template > 0 or charts_lib.is_in_file("error", log_helm)):
                print("  **Error generating template")
                status = "error_template"

        if key not in charts_pss:
            charts_pss[key] = dic_chart
        
        status = {
            "cache" : status,
            "chart_version" : version,
            "datetime" : now,
        }
        charts_pss[key]["status"] = status

        j+=1

        # if j % 10 == 0:
        #     print ("# Saving whole charts DB yaml")
        #     with open(charts_pss_filename, 'w') as file:
        #         yaml.dump(charts_pss, file)
        #     return charts_pss

        with open(charts_pss_filename, 'w') as file:
            yaml.dump(charts_pss, file)
    return charts_pss
