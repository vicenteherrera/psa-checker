
# --------------------------------------------------------------------------------------

GIT_SHA := $(shell git -c log.showSignature=false rev-parse HEAD 2>/dev/null)
GIT_TAG := $(shell bash -c 'TAG=$$(git -c log.showSignature=false \
	describe --tags --exact-match --abbrev=0 $(GIT_SHA) 2>/dev/null); echo "$${TAG:-dev}"')

LDFLAGS=-s -w \
        -X github.com/vicenteherrera/psa-checker/cmd/psa-checker.version=$(GIT_TAG) \
        -X github.com/vicenteherrera/psa-checker/cmd/psa-checker.commit=$(GIT_SHA) \
		-X github.com/vicenteherrera/psa-checker/cmd/psa-checker.date=$(date +"%Y-%m-%dT%H:%M:%S%z") \
		-X github.com/vicenteherrera/psa-checker/cmd/psa-checker.builtBy="makefile"

GO_VERSION := 1.26.1

TARGET_BIN=psa-checker
MAIN_DIR=./

CONTAINER_IMAGE=quay.io/vicenteherrera/psa-checker
CONTAINER_TAG=0.0.5
RUNSUDO := $(shell groups | grep ' docker \|com\.apple' 1>/dev/null || echo "sudo")

# --------------------------------------------------------------------------------------

.PHONY: all
# Run all build and test steps including tidy, build, run, test, and e2e
all: tidy build run test test-e2e

.PHONY: help
# Display available make targets and their descriptions
help:
	@awk '/^# / { comment = substr($$0, 3) } /^[a-zA-Z_-]+:/ { if (comment) { printf "  %-15s %s\n", $$1, comment; comment="" } }' $(MAKEFILE_LIST)

# -- Build targets

.PHONY: upgrade
# Upgrade all Go dependencies to latest versions (may introduce breaking changes)
upgrade:
	go get -u ./...

.PHONY: tidy
# Clean up go.mod and go.sum files, removing unused and adding missing deps
tidy:
	go mod tidy

.PHONY: mod_download
# Download all Go modules to ensure go.sum is up to date
mod_download:
	go mod download

.PHONY: build
# Build binary with version info for development (fast, unoptimized)
build:
	go build -ldflags "$(LDFLAGS)" -o ./release/${TARGET_BIN} ${MAIN_DIR}/main.go

.PHONY: build-release
# Build optimized release binary with version info (small, fast)
build-release: mod_download vet test-noginkgo
	CGO_ENABLED=0 go build -ldflags "$(LDFLAGS)" -o ./release/${TARGET_BIN} ${MAIN_DIR}/main.go

# strip ./release/${TARGET_BIN}

.PHONY: run
# Run binary with test manifest for manual testing and debugging
run:
	cd ./release && ./${TARGET_BIN} --level restricted --filename ../test/multi.yaml ||:

# Lint

.PHONY: lint
# Run all linting checks for Go, YAML, and Containerfile
lint: lint-go lint-yaml lint-containerfile

.PHONY: lint-go
# Lint Go code using golangci-lint
lint-go:
	golangci-lint run

.PHONY: lint-yaml
# Lint YAML files for syntax and best practices
lint-yaml:
	yamllint .

.PHONY: lint-containerfile
# Lint Containerfile for best practices and security
lint-containerfile:
	hadolint build/Containerfile

# Tests

.PHONY: test
# Run tests using Ginkgo with various options for randomization
test:
	ginkgo -randomize-all -randomize-suites -fail-on-pending -trace -race -cover -r -vv

.PHONY: test-noginkgo
# Run tests without Ginkgo for debugging and isolation
test-noginkgo:
	go test -v ./... -args -ginkgo.v

.PHONY: vet
# Run go vet to check for code issues like format strings
vet:
	go vet -v

.PHONY: test-e2e
# Run end to end tests
test-e2e:
	@echo "" ; echo "End to end tests"
	@cd ./test && ./test-success.sh $(E2E_TEST_FLAGS) || ( echo "[  error  ] Compliant manifests test error" && exit 1 )
	@cd ./test && ./test-fail.sh $(E2E_TEST_FLAGS) || ( echo "[  error  ] Non compliant manifests test error" && exit 1 )

.PHONY: test-e2e-container
# Run end to end tests using the latest version of the container image
test-e2e-container:
	@echo "" ; echo "End to end tests"
	@cd ./test && ./test-success.sh ---container || ( echo "[  error  ] Compliant manifests test error" && exit 1 )
	@cd ./test && ./test-fail.sh ---container || ( echo "[  error  ] Non compliant manifests test error" && exit 1 )

# dependencies

.PHONY: dependencies
# Check and print versions of all required dependencies
dependencies:
	go version
	ginkgo version
	golangci-lint --version
	yamllint --version
	hadolint --version
	yaml --version

.PHONY: install_ginkgo
# Install Ginkgo and Gomega for BDD-style Go testing
install_ginkgo:
	go install -mod=mod github.com/onsi/ginkgo/v2/ginkgo
	go get github.com/onsi/gomega/...

.PHONY: install_golangci-lint
# Install golangci-lint for Go code linting
install_golangci-lint:
	brew install golangci-lint
	brew upgrade golangci-lint

.PHONY: install_yamllint
# Install yamllint for YAML validation in tests
install_yamllint:
	pip install --user yamllint

.PHONY: install_yaml
# Install YAML parser for generating test manifests
install_yaml:
	pip install --user ruamel.yaml.cmd

# Container targets

.PHONY: cbuild-release
# Build the binary using a Go container to ensure a consistent build environment
cbuild-release:
	@echo "Building binary using Go ${GO_VERSION} container"
	${RUNSUDO} docker run --rm \
		--user $$(id -u):$$(id -g) \
		-e GOCACHE=/tmp/go-cache \
		-v "$$(pwd)":/workspace \
		-w /workspace \
		golang:${GO_VERSION} \
		make build-release

.PHONY: cshell
# Open shell in Go container with mounted directory
cshell:
	@echo "Opening shell in Go ${GO_VERSION} container"
	${RUNSUDO} docker run --rm -it \
		--name go-developer \
		--user $$(id -u):$$(id -g) \
		-e GOCACHE=/tmp/go-cache \
		-v "$$(pwd)":/workspace \
		-w /workspace \
		golang:${GO_VERSION} \
		bash

.PHONY: container-build
# Build the container image using the Containerfile in the build directory
container-build:
	@echo "Building container image"
	@$(RUNSUDO) docker build -f build/Containerfile -t ${CONTAINER_IMAGE}:${CONTAINER_TAG} .

.PHONY: container-run
# Run container image with test file mounted as current user
container-run:
	@echo "Running container image"
	@$(RUNSUDO) docker run --rm -it \
		-v "$$(pwd)"/test/in.yaml:/bin/in.yaml \
		-u $$(id -u $${USER}):$$(id -g $${USER}) \
		${CONTAINER_IMAGE}:${CONTAINER_TAG}

.PHONY: push
# Push the container image to the registry
push:
	${RUNSUDO} docker push ${CONTAINER_IMAGE}:${CONTAINER_TAG}

.PHONY: pull
# Pull the container image
pull:
	${RUNSUDO} docker pull ${CONTAINER_IMAGE}:${CONTAINER_TAG}
