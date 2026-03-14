#!/bin/bash

set -e

cd ../release

USE_CONTAINER=false
if [[ "${1:-}" == "--container" ]]; then
	USE_CONTAINER=true
fi

CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-docker}"
CONTAINER_IMAGE="${PSA_CHECKER_IMAGE:-quay.io/vicenteherrera/psa-checker:0.0.5}"
REPO_ROOT="$(cd .. && pwd)"

run_checker() {
	if [[ "$USE_CONTAINER" == "true" ]]; then
		"$CONTAINER_RUNTIME" run --rm \
			-v "$REPO_ROOT:/workspace" \
			-w /workspace/release \
			"$CONTAINER_IMAGE" "$@"
	else
		./psa-checker "$@"
	fi
}

run_checker --level baseline --filename ../test/pod-baseline.yaml 1>/dev/null 2>/dev/null
run_checker --level privileged --filename ../test/pod-privileged.yaml 1>/dev/null 2>/dev/null
run_checker --level restricted --filename ../test/pod-restricted.yaml 1>/dev/null 2>/dev/null

echo "[ success ] Compliant manifests pass checker"