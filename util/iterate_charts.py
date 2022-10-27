import yaml
import os
import sys

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

chart_levels_filename = "../docs/charts_levels.md"

print("# Reading helm_charts.yaml file with all charts")
f = open('helm_charts.yaml')
charts = yaml.safe_load(f)
f.close()

print("# Ordering charts alphabetically")
charts.sort(key=lambda x: x["repository"]["name"] + " " + get_chart_name( x["url"] ) )


print("# Checking latest chart")
if not os.path.exists(chart_levels_filename):
    print("Starting from the beginning of the list")
    list_md = open(chart_levels_filename, "a")
    list_md.write("| repo | chart | level | url | version | app version |\n")
    list_md.write("|------|------|------|------|------|------|\n")
    list_md.close()
    latest=""
else:
    last_line = read_n_to_last_line(chart_levels_filename)
    latest = last_line.split("|")[1].strip() + " " + last_line.split("|")[2].strip()
    print ("last repo and chart: " + latest)


print("# Iterating charts")
i=0
for dic_chart in charts:
    repo        = dic_chart["repository"]["name"]
    url         = dic_chart["repository"]["url"]
    version     = dic_chart["version"]
    app_version = dic_chart["app_version"]
    parts       = dic_chart["url"].split("/")
    chart        = get_chart_name( dic_chart["url"] )
    i+=1
    if ( repo + " " +  chart <= latest ):
        print("Skipping " + i + " " + repo + " " +  chart)
        continue

    print( "# ["+ str(i) + "/" + str(len(charts))+ "] " + repo + " " + chart + " " + url)
    os.system("helm repo add " + repo + " " + url)
    os.system("helm repo update " + repo)
    gen_template = os.system("helm template " + repo + "/" + chart + " --version " + version + " > temp.yaml")
    if ( gen_template >0 ):
        level = "error"
    else:
        baseline = os.system("cat temp.yaml | ../release/psa-checker --level baseline -f - >./logs/" + repo + "_" + chart + "_baseline.log")
        restricted = os.system("cat temp.yaml | ../release/psa-checker --level restricted -f - >./logs/" + repo + "_" + chart + "_restricted.log")
        if ( restricted == 0 and baseline == 0):
            level = "restricted"   
        elif (baseline==0):
            level = "baseline"
        else:
            level = "privileged"
        
    print("Level: " + level)
    list_md = open(chart_levels_filename, "a")
    list_md.write("| " + repo + " | " + chart + " | " + level + " | " + url + " | " + version + " | " + app_version + " |\n")
    list_md.close()

    # sys.exit()
