import yaml
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess
import time
from datetime import timedelta

import unicodedata
import re


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

def has_evaluation(chart_dict, eval_key):
    if eval_key in chart_dict and "score" in chart_dict[eval_key] and chart_dict[eval_key]["score"] != "":
        return True
    return False

def is_chart_error(chart_dict):
    if "pss" in chart_dict and "level" in chart_dict["pss"] and chart_dict["pss"]["level"][0:5]=="error":
        return True
    return False


def needs_update(repo, chart, dic_chart, charts_pss):
    key = repo + "__" + chart
    version = dic_chart["version"]
    if key not in charts_pss:
        return True
    if not "status" in charts_pss[key] or "chart_version" not in charts_pss[key]["status"] or charts_pss[key]["status"]["chart_version"] != version:
        return True
    return False

def needs_evaluation(repo, chart, tool, charts_db):
    key = repo + "__" + chart
    if key not in charts_db:
        print("  **Error, key %s not found in charts db" % key)
        return False
    if "status" not in charts_db[key] or "chart_version" not in charts_db[key]["status"]:
        print("  Status with version not found in charts db")
        return False
    if not "cache" in charts_db[key]["status"] or charts_db[key]["status"]["cache"] != "generated":
        print("  Chart not generated in charts db, status=%s" % charts_db[key]["status"]["cache"])
        return False
    if tool not in charts_db[key] or "chart_version" not in charts_db[key][tool]:
        print("  Tool %s not in status in charts db" % tool)
        return True
    if charts_db[key][tool]["chart_version"] != charts_db[key]["status"]["chart_version"]:
        print("  Chart version for tool not in charts db")
        return True
    print("  Tool %s up to date" % tool)
    return False
