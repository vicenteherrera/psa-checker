import yaml
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time
from datetime import timedelta




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

def evaluate_badrobot(template, log_badrobot):
    os.system("badrobot scan " + template + " > " + log_badrobot )
    os.system("cat " + log_badrobot + " | jq '[.[].score] | add' > " + log_badrobot + "_sum")
    with open(log_badrobot+"_sum") as f:
        score_badrobot = f.readline().strip('\n')
    return score_badrobot

def has_evaluation(chart_dict, eval_key):
    if eval_key in chart_dict and "score" in chart_dict[eval_key] and chart_dict[eval_key]["score"] != "":
        return True
    return False

def is_chart_error(chart_dict):
    if "pss" in chart_dict and "level" in chart_dict["pss"] and chart_dict["pss"]["level"][0:5]=="error":
        return True
    return False

