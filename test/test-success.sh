#!/bin/bash

set -e

cd ../release

./psa-checker --level baseline --filename ../test/pod-baseline.yaml 1>/dev/null 2>/dev/null
./psa-checker --level privileged --filename ../test/pod-privileged.yaml 1>/dev/null 2>/dev/null
./psa-checker --level restricted --filename ../test/pod-restricted.yaml 1>/dev/null 2>/dev/null

echo "[ success ] Compliant manifests pass checker"