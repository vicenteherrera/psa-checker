.PHONY: build test

TARGET_BIN=psa-checker
MAIN_DIR=./
CONTAINER_IMAGE=vicenteherrera/psa-checker

all: update build run test-e2e

update:
	go mod tidy

build:
	go build -o ./release/${TARGET_BIN} ${MAIN_DIR}/main.go

build-release:
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -ldflags="-s" -o ./release/${TARGET_BIN} ${MAIN_DIR}/main.go
	strip ./release/${TARGET_BIN}

run:
	cd ./release && ./${TARGET_BIN} --level restricted --filename ../test/multi.yaml ||:

# Tests

test:
	ginkgo -randomize-all -randomize-suites -fail-on-pending -trace -race -progress -cover -r -v

test-noginkgo:
	go test -v ./... -args -ginkgo.v

test-e2e:
	@cd ./test && ./test-success.sh || ( echo "[  error  ] Compliant manifests test error" && exit 1 )
	@cd ./test && ./test-fail.sh || ( echo "[  error  ] Non compliant manifests test error" && exit 1 )

# dependencies

dependecies:
	go version
	ginkgo version

install_ginkgo:
	go install -mod=mod github.com/onsi/ginkgo/v2/ginkgo
	go get github.com/onsi/gomega/...

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
