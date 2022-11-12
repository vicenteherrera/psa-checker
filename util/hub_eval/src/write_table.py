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
count = {
    "total":0,
    "privileged":0,
    "baseline":0,
    "restricted":0,
    "error_download":0,
    "error_template":0,
}
calpha = {}
for l in ascii_lowercase:
    calpha[l]=0

print("# Counting")
keys_pss = charts_pss.keys()    
for key in keys_pss:
    dic_chart = charts_pss[key]
    level = "unknown"
    i += 1
    calpha[dic_chart["repository"]["name"][0]] += 1
    if "pss" in dic_chart:
        level = dic_chart["pss"]["level"]
    count["total"] +=1
    if level not in count:
        count [level] = 1
    else:
        count[level] += 1

    print( "# ["+ str(i) + "/" + str(len(charts_pss))+ "] " + dic_chart["repository"]["name"] + level)

for key in count.keys():
    list_md.write(key.capitalize() + ": " + str(count[key]) + " ")
    list_md.write( "(" + str(round(100*count[key]/count["total"],2))+"%)\n" )

# Create index links
index = "[main](./charts_level.md) "
for l in ascii_lowercase:
    index += "["+l+"("+str(calpha[l])+")](./charts_level_"+l+".md) "

list_md.write("\n\n")
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
        list_md.write(index)
        list_md.write("\n\n| repo | chart | level | version | app version | url | \n")
        list_md.write("|------|------|------|------|------|------|\n")

    level = ""
    if "pss" in dic_chart:
        level = dic_chart["pss"]["level"]

    print( "# ["+ str(i) + "/" + str(len(keys_pss))+ "] " + repo + " " + chart + " " + level)

    list_md.write("| " + repo + " | " + chart + " | " + level  + " | " + version + " | " + app_version + " | " +  url + " |\n")

    # sys.exit()


list_md.close()
