import os
import yaml
import tools
import templates

# -----------------------------------------------------------------------

chart_levels_filename = r'./result/charts_levels.md'
charts_source_filename = r'./result/helm_charts.yaml'
charts_pss_filename = r'./result/helm_charts_pss.yaml'

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

print("# Downloading charts and generating templates")
charts_pss = templates.generate(charts_source, charts_pss, charts_pss_filename)

tools.evaluate(charts_source, charts_pss, charts_pss_filename)
