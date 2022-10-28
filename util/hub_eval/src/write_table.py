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


    print("# Iterating charts")
    i=0
    now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    count = {
        "total":0,
        "privileged":0,
        "baseline":0,
        "restricted":0
    }

    print("# Counting")
    for dic_chart in charts_source:
        level = "unknown"
        i += 1
        if "pss" in dic_chart:
            level = dic_chart["pss"]["level"]
        count["total"] +=1
        if level not in count:
            count [level] = 1
        else:
            count[level] +=1
    
        print( "# ["+ str(i) + "/" + str(len(charts_source))+ "] " + dic_chart["repository"]["name"] + level)

    for key in count.keys():
        list_md.write(key.capitalize() + ": " + str(count[key]) + " ")
        list_md.write( "(" + str(round(100*count[key]/count["total"],2))+"%)\n" )


    print("# Writing header")
    list_md.write("\n| repo | chart | level | url | version | app version |\n")
    list_md.write("|------|------|------|------|------|------|\n")

    print("# Iterating all charts")
    i=0
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
