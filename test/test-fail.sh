#!/bin/bash

cd ../release

./psa-checker --level baseline --filename ../test/pod-privileged.yaml 1>/dev/null 2>/dev/null
[ $? -ne 1 ] && exit 1
./psa-checker --level restricted --filename ../test/pod-baseline.yaml 1>/dev/null 2>/dev/null
[ $? -ne 1 ] && exit 1
./psa-checker --level restricted --filename ../test/pod-baseline.yaml 1>/dev/null 2>/dev/null
[ $? -ne 1 ] && exit 1

# Test for non-existent file
output=$(./psa-checker --filename nonexistent.yaml 2>&1)
[ $? -ne 1 ] && exit 1
if [[ "$output" != *"no such file or directory"* ]]; then exit 1; fi

echo "[ success ] Non compliant manifests succesfully flagged"