.PHONY: build test

TARGET_BIN=psa-checker
MAIN_DIR=./
CONTAINER_IMAGE=vicenteherrera/psa-checker

all: upgrade build run test test-e2e

upgrade:
	go mod tidy

update:
	go mod download

build:
	go build -o ./release/${TARGET_BIN} ${MAIN_DIR}/main.go

vet:
	go vet -v	

build-release: update vet test-noginkgo
	CGO_ENABLED=0 go build -ldflags="-s" -o ./release/${TARGET_BIN} ${MAIN_DIR}/main.go

# strip ./release/${TARGET_BIN}

run:
	cd ./release && ./${TARGET_BIN} --level restricted --filename ../test/multi.yaml ||:

# Lint

lint: lint-go lint-yaml lint-containerfile

lint-go:
	golangci-lint run

lint-yaml:
	yamllint .

lint-containerfile:
	hadolint build/Containerfile

# Tests

test:
	ginkgo -randomize-all -randomize-suites -fail-on-pending -trace -race -cover -r -vv

test-noginkgo:
	go test -v ./... -args -ginkgo.v

test-e2e:
	@echo "" ; echo "End to end tests"
	@cd ./test && ./test-success.sh || ( echo "[  error  ] Compliant manifests test error" && exit 1 )
	@cd ./test && ./test-fail.sh || ( echo "[  error  ] Non compliant manifests test error" && exit 1 )

# dependencies

dependencies:
	go version
	ginkgo version
	golangci-lint --version
	yamllint --version
	hadolint --version
	yaml --version

install_ginkgo:
	go install -mod=mod github.com/onsi/ginkgo/v2/ginkgo
	go get github.com/onsi/gomega/...

install_golangci-lint:
	brew install golangci-lint
	brew upgrade golangci-lint

install_yamllint:
	pip install --user yamllint

install_yaml:
	pip install --user ruamel.yaml.cmd

# Container targets

container-build:
	@echo "Building container image"
	@if groups $$USER | grep -q '\bdocker\b'; then RUNSUDO="" ; else RUNSUDO="sudo" ; fi && \
	    $$RUNSUDO docker build -f build/Containerfile -t ${CONTAINER_IMAGE} .

container-run:
	@echo "Running container image"
	@if groups $$USER | grep -q '\bdocker\b'; then RUNSUDO="" ; else RUNSUDO="sudo" ; fi && \
	    $$RUNSUDO docker run --rm -it \
		-v "$$(pwd)"/test/in.yaml:/bin/in.yaml \
		-u $$(id -u $${USER}):$$(id -g $${USER}) \
		${CONTAINER_IMAGE}

container-build-run: container-build container-run
