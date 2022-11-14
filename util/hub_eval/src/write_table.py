import yaml
import os
import sys
from datetime import datetime
from string import ascii_lowercase

def get_chart_name(url):
    parts = url.split("/")
    user  = parts[ len(parts) - 1 ]
    return user

doc_filename = r'./result/charts_levels'
charts_pss_filename = r'./result/helm_charts_pss.yaml'
logs_dir = r'./result/logs'
check_source = True

print("# Reading charts")
file = open(charts_pss_filename, 'r')
charts_pss = yaml.safe_load(file)
file.close()

# print("# Ordering charts alphabetically")
# charts_source.sort(key=lambda x: x["repository"]["name"] + " " + get_chart_name( x["url"] ) )

list_md = open(doc_filename+".md", "w")
print("# Iterating charts")
i=0
now = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
header = "[Go to root documentation](https://vicenteherrera.com/psa-checker)\n\n## Artifact Hub's Helm charts evaluation\n\n"
count = {
    "total":0,
    "privileged":0,
    "baseline":0,
    "restricted":0,
    "error_download":0,
    "error_template":0,
}
brbuckets = {}
calpha = {}
for l in ascii_lowercase:
    calpha[l]=0

print("# Counting")
date = ""
keys_pss = charts_pss.keys()    
for key in keys_pss:
    dic_chart = charts_pss[key]
    level = "unknown"
    i += 1
    calpha[dic_chart["repository"]["name"][0]] += 1
    if "pss" in dic_chart:
        if dic_chart["pss"]["date"] > date:
            date = dic_chart["pss"]["date"]
        level = dic_chart["pss"]["level"]
        if "score_badrobot" in dic_chart["pss"]:
            if dic_chart["pss"]["score_badrobot"] in brbuckets:
                brbuckets[dic_chart["pss"]["score_badrobot"]] += 1
            else:
                brbuckets[dic_chart["pss"]["score_badrobot"]] = 1
    count["total"] +=1
    if level not in count:
        count [level] = 1
    else:
        count[level] += 1
    print( "# ["+ str(i) + "/" + str(len(charts_pss))+ "] " + dic_chart["repository"]["name"] + level)

date = "Evaluation date: " + date + "\n"
list_md.write(header + date + "\n### Pod Security Standards (PSS)\n\n")
list_md.write("| Category | Quantity | Percentage |\n|------|------|------|\n")
for key in count.keys():
    list_md.write("| " + key.capitalize() + " | " + str(count[key]) + " | ")
    list_md.write( str(round(100*count[key]/count["total"],2))+"% |\n" )
list_md.write("\n")
list_md.write("Legend:\n")
list_md.write(" * Privileged, Baseline, Restricted: doesn’t account CRDs that could create pods\n")
list_md.write(" * Error_download: Downloading the template from original source wasn’t possible\n")
list_md.write(" * Error_template: Rendering the template without providing parameters resulted in error\n")
list_md.write(" * No_pod_object_but_crd: The chart didn’t render any object that can create pods, but has CRD that could do so\n")
list_md.write(" * No_pod_object_no_crd: The chart didn’t render any object that can create pods nor CRDs\n")
list_md.write(" * Version_not_evaluable: The cart includes deployment, daemonset, etc. of v1beta1 that can’t be evaluated by the library\n")
list_md.write("\n")

list_md.write("### BadRobot evaluation buckets\n\n")
list_md.write("[BadRobot](https://github.com/controlplaneio/badrobot) scores how secure Kubernetes operators are.\n")
list_md.write("| Score | Number of charts |\n|------|------|\n")
keys = brbuckets.keys()
for key in keys:
    list_md.write("| " + str(key) + " | " + str(brbuckets[key]) + " |\n")


list_md.write("\n### Charts list\n\n")

# Create index links
index = "[main](./charts_levels)&nbsp; "
for l in ascii_lowercase:
    index += "["+l.upper()+"("+str(calpha[l])+")](./charts_levels_"+l+")&nbsp; "
list_md.write("Alphabetical list of all repositories (number of charts in parenthesis):\n\n")
list_md.write(index)

print("# Iterating all charts")
i=0
last_letter=""
keys_pss = charts_pss.keys()    
for key in keys_pss:
    dic_chart = charts_pss[key]
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart        = get_chart_name( dic_chart["url"] )
    letter = repo[0]
    i+=1

    if letter != last_letter:
        last_letter = letter
        print("# Writing header: "+letter)
        list_md.close()
        list_md = open(doc_filename+"_"+letter+".md", "w")
        list_md.write(header + date + "\n" + index)
        list_md.write("\n\n| repo | chart | PSS level | BR score | chart version | app version |\n")
        list_md.write("|------|------|------|------|------|------|\n")

    level = ""
    brscore = ""
    if "pss" in dic_chart:
        level = dic_chart["pss"]["level"]
        if "score_badrobot" in dic_chart["pss"]:
            brscore = dic_chart["pss"]["score_badrobot"]
    print( "# ["+ str(i) + "/" + str(len(keys_pss))+ "] " + repo + " " + chart + " " + level)
    list_md.write("| [" + repo + "](" + url + ") | " + chart + " | " + level  + " | " + brscore  + " | " + version + " | " + app_version  + " |\n")
    # sys.exit()


list_md.close()
