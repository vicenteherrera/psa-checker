

all: evaluate generate_table

download_charts_info:
	helm search hub -o yaml > result/helm_charts.yaml

evaluate:
	python3 src/iterate_charts.py

reset-evaluate:
	rm result/helm_charts_pss.yaml ||:
	rm result/logs/* ||:
	$(MAKE) evaluate

generate_table:
	python3 src/write_table.py

