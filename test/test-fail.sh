#!/bin/bash

cd ../release

USE_CONTAINER=false
if [[ "${1:-}" == "--container" ]]; then
	USE_CONTAINER=true
fi

CONTAINER_IMAGE_TAG=0.0.5
REPO_ROOT="$(cd .. && pwd)"

run_checker() {
	if [[ "$USE_CONTAINER" == "true" ]]; then
		docker run --rm \
			-v "$REPO_ROOT:/workspace" \
			-w /workspace/release \
			quay.io/vicenteherrera/psa-checker: "$@"
	else
		./psa-checker "$@"
	fi
}

run_checker --level baseline --filename ../test/pod-privileged.yaml 1>/dev/null 2>/dev/null
[ $? -ne 1 ] && exit 1
run_checker --level restricted --filename ../test/pod-baseline.yaml 1>/dev/null 2>/dev/null
[ $? -ne 1 ] && exit 1
run_checker --level restricted --filename ../test/pod-baseline.yaml 1>/dev/null 2>/dev/null
[ $? -ne 1 ] && exit 1

# Test for non-existent file
output=$(run_checker --filename nonexistent.yaml 2>&1)
[ $? -ne 1 ] && exit 1
if [[ "$output" != *"no such file or directory"* ]]; then exit 1; fi

# Test for empty stdin input
output=$(printf '' | run_checker --filename - --level baseline 2>&1)
[ $? -ne 1 ] && exit 1
if [[ "$output" != *"empty input stream"* ]]; then exit 1; fi

echo "[ success ] Non compliant manifests succesfully flagged"