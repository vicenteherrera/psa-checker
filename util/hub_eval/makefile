

all: evaluate generate_table

download_charts_info:
	helm search hub -o yaml > result/helm_charts.yaml

evaluate:
	python3 hub_eval/iterate_charts.py

reset:
	rm result/helm_charts_pss.yaml ||:

full-reset: download_charts_info
	rm result/helm_charts_pss.yaml ||:
	rm result/logs/* ||:

generate_table:
	python3 hub_eval/write_table.py

prepare_docs:
	cp ../../README.md ../../../psa-docs/
	sed -r s#\<\/?div.*\>##g -i ../../../psa-docs/README.md
	cp ../../LICENSE.txt ../../../psa-docs/
	cp ./result/*.md ../../../psa-docs/
