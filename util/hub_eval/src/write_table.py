import yaml
import os
import sys
from datetime import datetime

def get_chart_name(url):
    parts = url.split("/")
    user  = parts[ len(parts) - 1 ]
    return user

psa_version = "0.0.1"
doc_filename = r'./result/charts_levels.md'
charts_pss_filename = r'./result/helm_charts_pss.yaml'
logs_dir = r'./result/logs'
check_source = True

print("# Reading charts")
file = open(charts_pss_filename, 'r')
charts_source = yaml.safe_load(file)
file.close()

print("# Ordering charts alphabetically")
charts_source.sort(key=lambda x: x["repository"]["name"] + " " + get_chart_name( x["url"] ) )

with open(doc_filename, "w") as list_md:

    print("# Writing header")
    list_md.write("| repo | chart | level | url | version | app version |\n")
    list_md.write("|------|------|------|------|------|------|\n")

    print("# Iterating charts")
    i=0
    now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    for dic_chart in charts_source:
        repo        = dic_chart["repository"]["name"]
        url         = dic_chart["repository"]["url"]
        version     = dic_chart["version"]
        app_version = dic_chart["app_version"]
        parts       = dic_chart["url"].split("/")
        chart        = get_chart_name( dic_chart["url"] )
        i+=1

        level = ""
        if "pss" in dic_chart:
            level = dic_chart["pss"]["level"]

        print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + repo + " " + chart + " " + level)

        list_md.write("| " + repo + " | " + chart + " | " + level + " | " + url + " | " + version + " | " + app_version + " |\n")

        # sys.exit()
