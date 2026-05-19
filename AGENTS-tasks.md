# PSA Checker - Potential Improvements and Tasks

This document outlines potential improvements to the PSA Checker project, organized by category. Each task includes a description of why it would improve the project, implementation guidance, and testing recommendations.

## Table of Contents

1. [Critical Bug Fixes & Code Quality](#1-critical-bug-fixes--code-quality)
2. [Features from Existing TODOs](#2-features-from-existing-todos)
3. [New User Experience Features](#3-new-user-experience-features)
4. [Testing Improvements](#4-testing-improvements)
5. [Performance Improvements](#5-performance-improvements)
6. [Documentation Improvements](#6-documentation-improvements)
7. [Security & Operations](#7-security--operations)

---

## 1. Critical Bug Fixes & Code Quality

### 1.1 Replace panic() with Proper Error Handling

**Location:** `pkg/analyzer/psaEvaluator.go` lines 50, 54, 71, 77, 93

**Why:** Using `panic()` for error handling is a Go anti-pattern. It makes the program crash unexpectedly instead of gracefully handling errors. This is especially problematic in CLI tools that users expect to handle errors gracefully.

**How to Implement:**
1. Replace all `panic(err)` calls with `return response, err`
2. Update function signatures to return errors properly
3. Ensure callers handle these errors appropriately
4. For truly unrecoverable errors, log them and exit with a proper error message

**Example:**
```go
// Before:
latest, err := api.ParseVersion("latest")
if err != nil {
    panic(err)
}

// After:
latest, err := api.ParseVersion("latest")
if err != nil {
    return response, fmt.Errorf("failed to parse PSS version: %w", err)
}
```

**Testing:**
- **Unit Test:** Create test cases with invalid PSS versions, malformed YAML, and invalid level strings
- **Test File:** Add to `pkg/analyzer/psaEvaluator_test.go`

```go
var _ = Describe("PsaEvaluator Error Handling", func() {
    Context("When given invalid level", func() {
        It("should return error instead of panicking", func() {
            evaluator := NewPsaEvaluator()
            yamlContent := []byte("apiVersion: v1\nkind: Pod\nmetadata:\n  name: test")
            response, err := evaluator.Evaluate(yamlContent, "invalid-level")
            Expect(err).To(HaveOccurred())
            Expect(response.AnalysisStatus).To(Equal("error"))
        })
    })

    Context("When given malformed YAML", func() {
        It("should return error gracefully", func() {
            evaluator := NewPsaEvaluator()
            yamlContent := []byte("{ invalid yaml }{")
            response, err := evaluator.Evaluate(yamlContent, "baseline")
            Expect(err).To(HaveOccurred())
        })
    })
})
```

---

### 1.3 Implement Structured Logging

**Location:** Throughout `pkg/analyzer/psaEvaluator.go`

**Why:** Current code uses `fmt.Printf` which writes directly to stdout, mixing informational output with actual results. This makes it difficult to:
- Parse output programmatically
- Control verbosity levels
- Redirect logs vs. results
- Integrate with logging systems

**How to Implement:**
1. Add a logging library (e.g., `log/slog` from stdlib or `github.com/rs/zerolog`)
2. Add a `--quiet`, `--verbose`, and `--debug` flags
3. Replace all `fmt.Printf` calls with appropriate log levels
4. Separate evaluation results from informational logging

**Example:**
```go
// Add to pkg/analyzer/psaEvaluator.go
import "log/slog"

type psaEvaluator struct {
    logger *slog.Logger
}

func NewPsaEvaluator(logger *slog.Logger) PsaEvaluator {
    return &psaEvaluator{logger: logger}
}

// Usage:
e.logger.Info("Evaluating object", "kind", gKV.Kind, "name", name)
e.logger.Debug("PSS level check", "level", levelVersion.Level, "version", levelVersion.Version)
e.logger.Warn("Check failed", "check", i, "reason", results[i].ForbiddenReason)
```

**Add to root.go:**
```go
var verbose bool
var quiet bool
var debug bool

rootCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Verbose output")
rootCmd.Flags().BoolVarP(&quiet, "quiet", "q", false, "Quiet mode (only errors)")
rootCmd.Flags().BoolVar(&debug, "debug", false, "Debug output")
```

**Testing:**
- **Unit Test:** Verify log messages are produced at appropriate levels
- **E2E Test:** Test different verbosity flags produce expected output

```go
var _ = Describe("Logging Levels", func() {
    It("should respect quiet mode", func() {
        // Capture log output and verify only errors appear
    })

    It("should show detailed info in verbose mode", func() {
        // Capture log output and verify verbose messages appear
    })
})
```

---

### 1.4 Consistent Error Message Capitalization

**Location:** Various error messages throughout the codebase

**Why:** Go convention is to use lowercase for error messages (unless starting with proper nouns or acronyms) since they're often wrapped in context.

**How to Implement:**
1. Audit all `errors.New()` and `fmt.Errorf()` calls
2. Change to lowercase unless starting with proper noun
3. Ensure error messages don't end with punctuation

**Example:**
```go
// Before:
errors.New("Empty imput stream")

// After:
errors.New("empty input stream")
```

**Testing:**
- **Code Review:** Use linter like `golangci-lint` with `errcheck` and `errorlint` enabled
- **Unit Tests:** Verify error messages in existing tests

---

## 2. Features from Existing TODOs

### 2.1 Configurable PSS Version Parameter

**Location:** `pkg/analyzer/psaEvaluator.go` line 47

**Why:** Currently the PSS version is hardcoded to "latest". Different Kubernetes versions support different PSS versions. Users may want to test against specific PSS versions for compatibility with their clusters.

**How to Implement:**
1. Add `--pss-version` flag to root command
2. Pass version parameter through to evaluator
3. Default to "latest" for backward compatibility
4. Validate version string against known PSS versions

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().StringP("pss-version", "p", "latest", "Pod Security Standard version (e.g., 'latest', 'v1.26', 'v1.25')")
viper.BindPFlag("pss-version", rootCmd.Flags().Lookup("pss-version"))
```

In `pkg/analyzer/client.go`:
```go
type client struct {
    filepath   string
    level      string
    pssVersion string
}

func NewClient(filepath string, level string, pssVersion string) Client {
    return &client{
        filepath:   filepath,
        level:      level,
        pssVersion: pssVersion,
    }
}
```

In `pkg/analyzer/psaEvaluator.go`:
```go
func (e *psaEvaluator) Evaluate(stream []byte, levelString string, versionString string) (AnalyzerResponse, error) {
    // Replace hardcoded "latest" with versionString parameter
    version, err := api.ParseVersion(versionString)
    if err != nil {
        return response, fmt.Errorf("invalid PSS version '%s': %w", versionString, err)
    }
    // ... rest of implementation
}
```

**Testing:**
- **Unit Tests:** Test with different PSS versions

```go
var _ = Describe("PSS Version Support", func() {
    It("should evaluate with latest version", func() {
        evaluator := NewPsaEvaluator()
        yamlContent := testPodYAML
        response, err := evaluator.Evaluate(yamlContent, "baseline", "latest")
        Expect(err).NotTo(HaveOccurred())
    })

    It("should evaluate with specific version", func() {
        evaluator := NewPsaEvaluator()
        yamlContent := testPodYAML
        response, err := evaluator.Evaluate(yamlContent, "baseline", "v1.26")
        Expect(err).NotTo(HaveOccurred())
    })

    It("should return error for invalid version", func() {
        evaluator := NewPsaEvaluator()
        yamlContent := testPodYAML
        response, err := evaluator.Evaluate(yamlContent, "baseline", "invalid")
        Expect(err).To(HaveOccurred())
    })
})
```

- **E2E Tests:** Add to `test/test-success.sh`

```bash
# Test with specific PSS version
./release/psa-checker -f test/pod-baseline.yaml -l baseline --pss-version v1.26
if [ $? -ne 0 ]; then
    echo "FAIL: PSS version v1.26 should work"
    exit 1
fi
echo "PASS: PSS version v1.26 works"
```

---

### 2.2 Break-on-First-Error Flag

**Location:** `pkg/analyzer/psaEvaluator.go` line 85, `cmd/psa-checker/root.go` line 81 (commented out)

**Why:** When evaluating large manifests with many objects, users may want the tool to exit immediately on the first violation for faster feedback, especially in CI/CD pipelines.

**How to Implement:**
1. Uncomment and implement the `--break` / `-b` flag
2. Pass this flag to the evaluator
3. Return immediately on first non-compliant object

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().BoolP("break", "b", false, "Stop evaluation on first non-compliant object")
viper.BindPFlag("break", rootCmd.Flags().Lookup("break"))
```

In `pkg/analyzer/psaEvaluator.go`:
```go
type psaEvaluator struct {
    breakOnError bool
}

func NewPsaEvaluator(breakOnError bool) PsaEvaluator {
    return &psaEvaluator{breakOnError: breakOnError}
}

func (e *psaEvaluator) Evaluate(stream []byte, levelString string) (AnalyzerResponse, error) {
    // ... existing code ...

    allowed, err := e.evaluate(obj, gKV, levelVersion)
    if err != nil {
        response.AnalysisStatus = "error"
        return response, err
    }
    response.Allowed = response.Allowed && allowed

    // Add break on error logic
    if e.breakOnError && !allowed {
        response.AnalysisStatus = "stopped_on_error"
        return response, nil
    }
}
```

**Testing:**
- **Unit Test:**

```go
var _ = Describe("Break on Error", func() {
    Context("With multiple non-compliant objects", func() {
        It("should stop on first error when break flag is set", func() {
            evaluator := NewPsaEvaluator(true) // break on error = true
            multiDocYAML := `---
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod-1
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      privileged: true
---
apiVersion: v1
kind: Pod
metadata:
  name: privileged-pod-2
spec:
  containers:
  - name: test
    image: nginx
    securityContext:
      privileged: true`

            response, err := evaluator.Evaluate([]byte(multiDocYAML), "baseline")
            Expect(err).NotTo(HaveOccurred())
            Expect(response.Allowed).To(BeFalse())
            Expect(response.AnalysisStatus).To(Equal("stopped_on_error"))
        })

        It("should evaluate all objects when break flag is false", func() {
            evaluator := NewPsaEvaluator(false)
            // Same test but should process all objects
        })
    })
})
```

- **E2E Test:** Add to `test/test-fail.sh`

```bash
# Test break on first error
./release/psa-checker -f test/multi-fail.yaml -l restricted --break
if [ $? -ne 1 ]; then
    echo "FAIL: Break on error should exit with code 1"
    exit 1
fi
echo "PASS: Break on error works correctly"
```

---

### 2.3 Verbose/Debug Output Flags

**Location:** Multiple TODOs in `pkg/analyzer/psaEvaluator.go` (lines 177, 187)

**Why:** Users need different levels of output detail. CI/CD may want minimal output, while debugging requires detailed information. Currently all output goes to stdout without control.

**How to Implement:**
1. Implement as part of Task 1.3 (Structured Logging)
2. Add verbosity levels: quiet, normal, verbose, debug
3. Control which messages are displayed at each level

**Code Changes:**
See Task 1.3 for implementation details

**Testing:**
- **E2E Tests:**

```bash
# Test quiet mode
output=$(./release/psa-checker -f test/pod-baseline.yaml -l baseline --quiet 2>&1)
lines=$(echo "$output" | wc -l)
if [ $lines -gt 1 ]; then
    echo "FAIL: Quiet mode should minimize output"
    exit 1
fi
echo "PASS: Quiet mode works"

# Test verbose mode
output=$(./release/psa-checker -f test/pod-baseline.yaml -l baseline --verbose 2>&1)
if ! echo "$output" | grep -q "Evaluating"; then
    echo "FAIL: Verbose mode should show detailed output"
    exit 1
fi
echo "PASS: Verbose mode works"
```

---

### 2.4 Configurable Handling of Non-Evaluable API Versions

**Location:** `pkg/analyzer/psaEvaluator.go` line 112

**Why:** When encountering API versions that can't be evaluated (e.g., deprecated v1beta1 objects), users may want different behaviors:
- Skip and continue (current default)
- Treat as failure (strict mode)
- Warn but allow (permissive mode)

**How to Implement:**
1. Add `--api-version-handling` flag with options: `skip`, `fail`, `warn`
2. Implement different behaviors based on flag
3. Default to `skip` for backward compatibility

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().String("api-version-handling", "skip",
    "How to handle non-evaluable API versions: 'skip', 'warn', 'fail'")
viper.BindPFlag("api-version-handling", rootCmd.Flags().Lookup("api-version-handling"))
```

In `pkg/analyzer/psaEvaluator.go`:
```go
type psaEvaluator struct {
    breakOnError        bool
    apiVersionHandling  string
    logger             *slog.Logger
}

func (e *psaEvaluator) evaluate(obj runtime.Object, gKV *schema.GroupVersionKind, levelVersion api.LevelVersion) (bool, error) {
    // When encountering non-evaluable versions
    if gKV.Group+gKV.Version != "appsv1" {
        msg := fmt.Sprintf("Version %s not evaluable for kind: %v", gKV.Version, gKV.Kind)

        switch e.apiVersionHandling {
        case "skip":
            e.logger.Debug(msg)
            return true, nil
        case "warn":
            e.logger.Warn(msg)
            return true, nil
        case "fail":
            e.logger.Error(msg)
            return false, fmt.Errorf("non-evaluable API version: %s for kind %s", gKV.Version, gKV.Kind)
        default:
            return true, nil
        }
    }
    // ... rest of implementation
}
```

**Testing:**
- **Unit Tests:**

```go
var _ = Describe("API Version Handling", func() {
    Context("With non-evaluable API version", func() {
        It("should skip in skip mode", func() {
            evaluator := NewPsaEvaluator(false, "skip", logger)
            // Use v1beta1 deployment
            response, err := evaluator.Evaluate(v1beta1DeploymentYAML, "baseline")
            Expect(err).NotTo(HaveOccurred())
            Expect(response.Allowed).To(BeTrue())
        })

        It("should fail in fail mode", func() {
            evaluator := NewPsaEvaluator(false, "fail", logger)
            response, err := evaluator.Evaluate(v1beta1DeploymentYAML, "baseline")
            Expect(err).To(HaveOccurred())
        })

        It("should warn in warn mode", func() {
            // Capture log output and verify warning
            evaluator := NewPsaEvaluator(false, "warn", logger)
            response, err := evaluator.Evaluate(v1beta1DeploymentYAML, "baseline")
            Expect(err).NotTo(HaveOccurred())
            Expect(response.Allowed).To(BeTrue())
            // Verify warning was logged
        })
    })
})
```

---

## 3. New User Experience Features

### 3.1 JSON Output Format

**Why:** CI/CD systems, security scanners, and automation tools benefit from structured, machine-readable output. JSON format enables:
- Easy parsing in scripts and tools
- Integration with security dashboards
- Programmatic analysis of results
- Better tool interoperability

**How to Implement:**
1. Add `--output` / `-o` flag with values: `text` (default), `json`, `json-pretty`
2. Create JSON output format structure
3. Marshal results to JSON when flag is set

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().StringP("output", "o", "text", "Output format: text, json, json-pretty")
viper.BindPFlag("output", rootCmd.Flags().Lookup("output"))
```

In `pkg/analyzer/model.go`:
```go
type AnalyzerResponse struct {
    Allowed        bool              `json:"allowed"`
    AnalysisStatus string            `json:"analysis_status"`
    Results        []ObjectResult    `json:"results,omitempty"`
    Summary        ResultSummary     `json:"summary"`
}

type ObjectResult struct {
    Kind      string         `json:"kind"`
    Name      string         `json:"name"`
    Namespace string         `json:"namespace,omitempty"`
    Allowed   bool           `json:"allowed"`
    Level     string         `json:"level"`
    Failures  []CheckFailure `json:"failures,omitempty"`
}

type CheckFailure struct {
    Check   string `json:"check"`
    Reason  string `json:"reason"`
    Detail  string `json:"detail"`
}

type ResultSummary struct {
    Total       int `json:"total_objects"`
    Compliant   int `json:"compliant"`
    NonCompliant int `json:"non_compliant"`
    Skipped     int `json:"skipped"`
}
```

In `cmd/psa-checker/root.go`:
```go
func formatOutput(response analyzer.AnalyzerResponse, level string, outputFormat string) error {
    switch outputFormat {
    case "json":
        jsonBytes, err := json.Marshal(response)
        if err != nil {
            return fmt.Errorf("failed to marshal JSON: %w", err)
        }
        fmt.Println(string(jsonBytes))
    case "json-pretty":
        jsonBytes, err := json.MarshalIndent(response, "", "  ")
        if err != nil {
            return fmt.Errorf("failed to marshal JSON: %w", err)
        }
        fmt.Println(string(jsonBytes))
    case "text":
    default:
        // Existing text output
        if response.Allowed {
            fmt.Fprintln(os.Stderr, "Manifest(s) comply with PSS level "+level)
        } else {
            fmt.Fprintln(os.Stderr, "Manifest(s) do not comply with PSS level "+level)
        }
    }
    return nil
}
```

**Testing:**
- **Unit Tests:**

```go
var _ = Describe("JSON Output", func() {
    It("should produce valid JSON", func() {
        response := AnalyzerResponse{
            Allowed: true,
            AnalysisStatus: "completed",
            Results: []ObjectResult{
                {Kind: "Pod", Name: "test", Allowed: true},
            },
        }

        jsonBytes, err := json.Marshal(response)
        Expect(err).NotTo(HaveOccurred())

        var parsed AnalyzerResponse
        err = json.Unmarshal(jsonBytes, &parsed)
        Expect(err).NotTo(HaveOccurred())
        Expect(parsed.Allowed).To(Equal(response.Allowed))
    })
})
```

- **E2E Tests:**

```bash
# Test JSON output
output=$(./release/psa-checker -f test/pod-baseline.yaml -l baseline --output json)
echo "$output" | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL: JSON output is not valid JSON"
    exit 1
fi

# Verify structure
allowed=$(echo "$output" | jq -r '.allowed')
if [ "$allowed" != "true" ]; then
    echo "FAIL: JSON output should show allowed=true"
    exit 1
fi
echo "PASS: JSON output works correctly"
```

---

### 3.2 SARIF Output Format

**Why:** SARIF (Static Analysis Results Interchange Format) is the standard format for security scanning tools. Support enables:
- Integration with GitHub Security tab
- Compatibility with security dashboards (Snyk, Aqua, etc.)
- Better DevSecOps workflows
- Standardized security reporting

**How to Implement:**
1. Add `--output sarif` option
2. Import SARIF library or build struct manually
3. Map PSS violations to SARIF format

**Code Changes:**

```go
// Add SARIF structure (simplified - use full spec or library)
type SARIFReport struct {
    Version string        `json:"version"`
    Schema  string        `json:"$schema"`
    Runs    []SARIFRun    `json:"runs"`
}

type SARIFRun struct {
    Tool    SARIFTool      `json:"tool"`
    Results []SARIFResult  `json:"results"`
}

type SARIFTool struct {
    Driver SARIFDriver `json:"driver"`
}

type SARIFDriver struct {
    Name            string `json:"name"`
    InformationUri  string `json:"informationUri"`
    Version         string `json:"version"`
}

type SARIFResult struct {
    RuleID  string        `json:"ruleId"`
    Level   string        `json:"level"`
    Message SARIFMessage  `json:"message"`
    Locations []SARIFLocation `json:"locations,omitempty"`
}

func convertToSARIF(response AnalyzerResponse) SARIFReport {
    // Convert AnalyzerResponse to SARIF format
}
```

**Testing:**
- **E2E Tests:**

```bash
# Test SARIF output
output=$(./release/psa-checker -f test/pod-privileged.yaml -l restricted --output sarif)
echo "$output" | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL: SARIF output is not valid JSON"
    exit 1
fi

# Verify SARIF schema
schema=$(echo "$output" | jq -r '."$schema"')
if [[ ! "$schema" =~ "sarif" ]]; then
    echo "FAIL: Not a valid SARIF document"
    exit 1
fi
echo "PASS: SARIF output works correctly"
```

---

### 3.3 Summary Statistics

**Why:** Users want to see high-level metrics about their evaluation:
- Total objects analyzed
- How many passed/failed
- Success rate percentage
- Quick understanding of overall compliance

**How to Implement:**
1. Track statistics during evaluation
2. Add summary section to output
3. Display in both text and JSON formats

**Code Changes:**

Already defined `ResultSummary` in model.go above. Update evaluator:

```go
func (e *psaEvaluator) Evaluate(stream []byte, levelString string) (AnalyzerResponse, error) {
    // ... existing code ...

    var stats struct {
        total        int
        compliant    int
        nonCompliant int
        skipped      int
    }

    for {
        // ... evaluation loop ...
        stats.total++

        if /* object was skipped */ {
            stats.skipped++
            continue
        }

        if allowed {
            stats.compliant++
        } else {
            stats.nonCompliant++
        }
    }

    response.Summary = ResultSummary{
        Total:        stats.total,
        Compliant:    stats.compliant,
        NonCompliant: stats.nonCompliant,
        Skipped:      stats.skipped,
    }

    return response, nil
}
```

Text output in root.go:
```go
fmt.Fprintln(os.Stderr, "\nSummary:")
fmt.Fprintf(os.Stderr, "  Total objects: %d\n", response.Summary.Total)
fmt.Fprintf(os.Stderr, "  Compliant: %d\n", response.Summary.Compliant)
fmt.Fprintf(os.Stderr, "  Non-compliant: %d\n", response.Summary.NonCompliant)
if response.Summary.Skipped > 0 {
    fmt.Fprintf(os.Stderr, "  Skipped: %d\n", response.Summary.Skipped)
}
```

**Testing:**
- **Unit Tests:**

```go
var _ = Describe("Summary Statistics", func() {
    It("should track compliant objects", func() {
        evaluator := NewPsaEvaluator()
        response, err := evaluator.Evaluate(compliantPodYAML, "baseline")
        Expect(err).NotTo(HaveOccurred())
        Expect(response.Summary.Total).To(Equal(1))
        Expect(response.Summary.Compliant).To(Equal(1))
        Expect(response.Summary.NonCompliant).To(Equal(0))
    })

    It("should track mixed results", func() {
        evaluator := NewPsaEvaluator()
        multiDoc := `---
# Compliant pod
apiVersion: v1
kind: Pod
...
---
# Non-compliant pod
apiVersion: v1
kind: Pod
...
---
# ServiceAccount (skipped)
apiVersion: v1
kind: ServiceAccount
...`
        response, err := evaluator.Evaluate([]byte(multiDoc), "baseline")
        Expect(err).NotTo(HaveOccurred())
        Expect(response.Summary.Total).To(Equal(3))
        Expect(response.Summary.Compliant).To(Equal(1))
        Expect(response.Summary.NonCompliant).To(Equal(1))
        Expect(response.Summary.Skipped).To(Equal(1))
    })
})
```

---

### 3.4 Output to File

**Why:** Users may want to save results to a file for:
- Documentation/audit trails
- Sharing with team members
- Processing with other tools
- Historical comparison

**How to Implement:**
1. Add `--output-file` flag
2. Write results to specified file instead of stdout
3. Support with all output formats

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().String("output-file", "", "Write output to file instead of stdout")
viper.BindPFlag("output-file", rootCmd.Flags().Lookup("output-file"))

// In RunE:
outputFile := viper.GetString("output-file")
if outputFile != "" {
    f, err := os.Create(outputFile)
    if err != nil {
        return fmt.Errorf("failed to create output file: %w", err)
    }
    defer f.Close()

    // Redirect output to file
    oldStdout := os.Stdout
    os.Stdout = f
    defer func() { os.Stdout = oldStdout }()
}
```

**Testing:**
- **E2E Tests:**

```bash
# Test output to file
./release/psa-checker -f test/pod-baseline.yaml -l baseline \
    --output json --output-file /tmp/psa-result.json

if [ ! -f /tmp/psa-result.json ]; then
    echo "FAIL: Output file was not created"
    exit 1
fi

cat /tmp/psa-result.json | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "FAIL: Output file does not contain valid JSON"
    exit 1
fi

rm /tmp/psa-result.json
echo "PASS: Output to file works correctly"
```

---

### 3.5 Multiple File Support

**Why:** Users often want to check multiple files in one command instead of running the tool multiple times.

**How to Implement:**
1. Allow multiple `-f` flags or comma-separated filenames
2. Aggregate results across all files
3. Show per-file and overall summary

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
// Change to StringSlice
rootCmd.Flags().StringSliceP("filename", "f", []string{}, "Files to test (can specify multiple)")
viper.BindPFlag("filename", rootCmd.Flags().Lookup("filename"))

// In RunE:
filenames := viper.GetStringSlice("filename")
if len(filenames) == 0 {
    return errors.New("at least one filename parameter is required")
}

var aggregatedResponse analyzer.AnalyzerResponse
aggregatedResponse.Allowed = true

for _, filename := range filenames {
    client := analyzer.NewClient(filename, level)
    response, err := client.AnalyzeFile()
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error processing %s: %v\n", filename, err)
        continue
    }

    aggregatedResponse.Allowed = aggregatedResponse.Allowed && response.Allowed
    aggregatedResponse.Results = append(aggregatedResponse.Results, response.Results...)
    // Aggregate summaries
}
```

**Testing:**
- **E2E Tests:**

```bash
# Test multiple files
./release/psa-checker -f test/pod-baseline.yaml -f test/deployment.yaml -l baseline
if [ $? -ne 0 ]; then
    echo "FAIL: Multiple file support failed"
    exit 1
fi

# Test with glob pattern (bonus)
./release/psa-checker -f "test/*.yaml" -l baseline
echo "PASS: Multiple file support works"
```

---

### 3.6 Namespace Filtering

**Why:** When analyzing cluster dumps with `kubectl get pods -A -oyaml`, users may only care about specific namespaces.

**How to Implement:**
1. Add `--namespace` and `--exclude-namespace` flags
2. Filter objects during evaluation
3. Support multiple values and wildcard patterns

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().StringSlice("namespace", []string{}, "Only evaluate objects in these namespaces")
rootCmd.Flags().StringSlice("exclude-namespace", []string{}, "Skip objects in these namespaces")
viper.BindPFlag("namespace", rootCmd.Flags().Lookup("namespace"))
viper.BindPFlag("exclude-namespace", rootCmd.Flags().Lookup("exclude-namespace"))
```

In `pkg/analyzer/psaEvaluator.go`:
```go
type psaEvaluator struct {
    // ... existing fields ...
    includeNamespaces []string
    excludeNamespaces []string
}

func (e *psaEvaluator) shouldEvaluate(namespace string) bool {
    // If include list is specified, namespace must be in it
    if len(e.includeNamespaces) > 0 {
        found := false
        for _, ns := range e.includeNamespaces {
            if matchNamespace(ns, namespace) {
                found = true
                break
            }
        }
        if !found {
            return false
        }
    }

    // Check exclude list
    for _, ns := range e.excludeNamespaces {
        if matchNamespace(ns, namespace) {
            return false
        }
    }

    return true
}

func matchNamespace(pattern, namespace string) bool {
    // Support wildcard matching: kube-*, *-system, etc.
    match, _ := filepath.Match(pattern, namespace)
    return match
}
```

**Testing:**
- **Unit Tests:**

```go
var _ = Describe("Namespace Filtering", func() {
    It("should include only specified namespaces", func() {
        evaluator := NewPsaEvaluator()
        evaluator.includeNamespaces = []string{"default", "app-*"}

        Expect(evaluator.shouldEvaluate("default")).To(BeTrue())
        Expect(evaluator.shouldEvaluate("app-frontend")).To(BeTrue())
        Expect(evaluator.shouldEvaluate("kube-system")).To(BeFalse())
    })

    It("should exclude specified namespaces", func() {
        evaluator := NewPsaEvaluator()
        evaluator.excludeNamespaces = []string{"kube-*"}

        Expect(evaluator.shouldEvaluate("default")).To(BeTrue())
        Expect(evaluator.shouldEvaluate("kube-system")).To(BeFalse())
        Expect(evaluator.shouldEvaluate("kube-public")).To(BeFalse())
    })
})
```

---

### 3.7 Exit Code Options

**Why:** Different CI/CD systems may want different exit code behaviors:
- Always exit 0 (report only, don't fail pipeline)
- Exit 1 only on errors (warnings OK)
- Exit with different codes for different failure types

**How to Implement:**
1. Add `--exit-code` flag with options: `standard` (default), `always-zero`, `error-only`
2. Modify exit logic based on flag

**Code Changes:**

In `cmd/psa-checker/root.go`:
```go
rootCmd.Flags().String("exit-code", "standard",
    "Exit code behavior: 'standard' (1 on violations), 'always-zero', 'error-only' (1 only on errors)")
viper.BindPFlag("exit-code", rootCmd.Flags().Lookup("exit-code"))

// In RunE:
exitCodeBehavior := viper.GetString("exit-code")
var exitCode int

switch exitCodeBehavior {
case "always-zero":
    exitCode = 0
case "error-only":
    if response.AnalysisStatus == "error" {
        exitCode = 1
    } else {
        exitCode = 0
    }
case "standard":
default:
    if response.Allowed {
        exitCode = 0
    } else {
        exitCode = 1
    }
}

os.Exit(exitCode)
```

**Testing:**
- **E2E Tests:**

```bash
# Test always-zero
./release/psa-checker -f test/pod-privileged.yaml -l restricted --exit-code always-zero
if [ $? -ne 0 ]; then
    echo "FAIL: always-zero should exit with 0"
    exit 1
fi

# Test error-only (non-compliance is not an error)
./release/psa-checker -f test/pod-privileged.yaml -l restricted --exit-code error-only
if [ $? -ne 0 ]; then
    echo "FAIL: error-only should exit with 0 for non-compliance"
    exit 1
fi

echo "PASS: Exit code options work correctly"
```

---

## 4. Testing Improvements

### 4.1 Add Benchmark Tests

**Why:** Performance regression detection and optimization guidance. Benchmarks help identify:
- Performance bottlenecks
- Impact of changes on speed
- Scalability limits

**How to Implement:**
1. Create benchmark tests for key operations
2. Test with various file sizes
3. Add to CI/CD for regression detection

**Code Changes:**

Create `pkg/analyzer/psaEvaluator_bench_test.go`:
```go
package analyzer_test

import (
    "testing"
    "github.com/vicenteherrera/psa-checker/pkg/analyzer"
)

func BenchmarkEvaluateSinglePod(b *testing.B) {
    evaluator := analyzer.NewPsaEvaluator()
    yamlContent := []byte(singlePodYAML)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = evaluator.Evaluate(yamlContent, "baseline")
    }
}

func BenchmarkEvaluateMultiDocument(b *testing.B) {
    evaluator := analyzer.NewPsaEvaluator()
    yamlContent := generateMultiDocYAML(100) // 100 objects

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = evaluator.Evaluate(yamlContent, "baseline")
    }
}

func BenchmarkEvaluateLargeDeployment(b *testing.B) {
    evaluator := analyzer.NewPsaEvaluator()
    yamlContent := generateLargeDeployment(50) // 50 containers

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = evaluator.Evaluate(yamlContent, "restricted")
    }
}

func BenchmarkEvaluateHelmChart(b *testing.B) {
    evaluator := analyzer.NewPsaEvaluator()
    // Use real Helm chart template output
    yamlContent := loadHelmChartTemplate()

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = evaluator.Evaluate(yamlContent, "baseline")
    }
}
```

Add to Makefile:
```makefile
.PHONY: bench
bench:
	@echo "Running benchmarks..."
	go test -bench=. -benchmem -run=^$$ ./pkg/analyzer

.PHONY: bench-compare
bench-compare:
	@echo "Running benchmarks and comparing to baseline..."
	go test -bench=. -benchmem -run=^$$ ./pkg/analyzer | tee new.txt
	benchstat old.txt new.txt
```

**Testing:**
```bash
# Run benchmarks
make bench

# Compare before/after changes
make bench > old.txt
# Make changes
make bench > new.txt
benchstat old.txt new.txt
```

---

### 4.2 Add Fuzz Testing

**Why:** Discover edge cases and potential crashes with randomly generated input. Helps find:
- Panic conditions
- Infinite loops
- Memory leaks
- Unexpected input handling issues

**How to Implement:**
1. Use Go's built-in fuzzing (Go 1.18+)
2. Fuzz YAML parser and evaluator
3. Add corpus of interesting test cases

**Code Changes:**

Create `pkg/analyzer/psaEvaluator_fuzz_test.go`:
```go
package analyzer_test

import (
    "testing"
    "github.com/vicenteherrera/psa-checker/pkg/analyzer"
)

func FuzzEvaluateYAML(f *testing.F) {
    // Seed corpus with known good and bad inputs
    f.Add([]byte("apiVersion: v1\nkind: Pod\nmetadata:\n  name: test"))
    f.Add([]byte("---\n"))
    f.Add([]byte(""))
    f.Add([]byte("{ invalid }"))
    f.Add([]byte(string(make([]byte, 10000)))) // Large input

    evaluator := analyzer.NewPsaEvaluator()

    f.Fuzz(func(t *testing.T, data []byte) {
        // Should not panic
        _, _ = evaluator.Evaluate(data, "baseline")
    })
}

func FuzzEvaluateLevel(f *testing.F) {
    // Test different level strings
    f.Add("baseline")
    f.Add("restricted")
    f.Add("privileged")
    f.Add("")
    f.Add("invalid")
    f.Add(string(make([]byte, 1000)))

    evaluator := analyzer.NewPsaEvaluator()
    validYAML := []byte("apiVersion: v1\nkind: Pod\nmetadata:\n  name: test")

    f.Fuzz(func(t *testing.T, level string) {
        // Should not panic
        _, _ = evaluator.Evaluate(validYAML, level)
    })
}
```

Add to Makefile:
```makefile
.PHONY: fuzz
fuzz:
	@echo "Running fuzz tests (ctrl-c to stop)..."
	go test -fuzz=FuzzEvaluateYAML -fuzztime=30s ./pkg/analyzer
	go test -fuzz=FuzzEvaluateLevel -fuzztime=30s ./pkg/analyzer
```

**Testing:**
```bash
# Run fuzzing
make fuzz

# Run with longer duration
go test -fuzz=FuzzEvaluateYAML -fuzztime=5m ./pkg/analyzer
```

---

### 4.3 Integration Tests with Real Helm Charts

**Why:** Ensure tool works with real-world Helm charts from popular projects. Tests realistic scenarios and validates compatibility.

**How to Implement:**
1. Create integration test suite
2. Download and template popular Helm charts
3. Validate expected PSS levels

**Code Changes:**

Create `test/integration/helm_test.go`:
```go
// +build integration

package integration_test

import (
    "os/exec"
    "testing"
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestHelmIntegration(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Helm Integration Suite")
}

var _ = Describe("Popular Helm Charts", func() {
    Context("nginx-ingress", func() {
        It("should pass baseline level", func() {
            cmd := exec.Command("helm", "template",
                "ingress-nginx",
                "ingress-nginx/ingress-nginx",
                "|",
                "../release/psa-checker",
                "-f", "-",
                "-l", "baseline")
            err := cmd.Run()
            Expect(err).NotTo(HaveOccurred())
        })
    })

    Context("prometheus-operator", func() {
        It("should identify non-compliant at restricted level", func() {
            // This chart has known violations
            cmd := exec.Command("bash", "-c",
                "helm template prometheus prometheus-community/kube-prometheus-stack | "+
                "../release/psa-checker -f - -l restricted")
            err := cmd.Run()
            Expect(err).To(HaveOccurred()) // Should fail
        })
    })

    // Add more popular charts
})
```

Add to Makefile:
```makefile
.PHONY: test-integration
test-integration:
	@echo "Running integration tests with real Helm charts..."
	helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update
	go test -tags=integration -v ./test/integration/...
```

**Testing:**
```bash
make test-integration
```

---

### 4.4 Table-Driven Tests for Kubernetes Versions

**Why:** Ensure compatibility across different Kubernetes versions and their respective PSS versions.

**How to Implement:**
1. Create table of Kubernetes versions and expected behaviors
2. Test each version systematically
3. Document compatibility matrix

**Code Changes:**

In `pkg/analyzer/psaEvaluator_test.go`:
```go
var _ = Describe("Kubernetes Version Compatibility", func() {
    type versionTest struct {
        k8sVersion   string
        pssVersion   string
        manifestFile string
        level        string
        shouldPass   bool
        description  string
    }

    DescribeTable("PSS version compatibility",
        func(test versionTest) {
            evaluator := NewPsaEvaluator()
            yamlContent := loadTestFile(test.manifestFile)

            response, err := evaluator.Evaluate(yamlContent, test.level, test.pssVersion)

            Expect(err).NotTo(HaveOccurred())
            if test.shouldPass {
                Expect(response.Allowed).To(BeTrue(), test.description)
            } else {
                Expect(response.Allowed).To(BeFalse(), test.description)
            }
        },

        Entry("K8s 1.25 baseline", versionTest{
            k8sVersion:   "1.25",
            pssVersion:   "v1.25",
            manifestFile: "pod-baseline.yaml",
            level:        "baseline",
            shouldPass:   true,
            description:  "Baseline pod should pass on K8s 1.25",
        }),

        Entry("K8s 1.26 restricted", versionTest{
            k8sVersion:   "1.26",
            pssVersion:   "v1.26",
            manifestFile: "pod-baseline.yaml",
            level:        "restricted",
            shouldPass:   false,
            description:  "Baseline pod should fail restricted on K8s 1.26",
        }),

        Entry("K8s 1.27 latest", versionTest{
            k8sVersion:   "1.27",
            pssVersion:   "latest",
            manifestFile: "pod-restricted.yaml",
            level:        "restricted",
            shouldPass:   true,
            description:  "Restricted pod should pass on latest",
        }),

        // Add more version combinations
    )
})
```

---

### 4.5 Error Path Testing

**Why:** Many tests focus on happy paths. Need comprehensive error case coverage.

**How to Implement:**
1. Test all error conditions
2. Verify error messages are helpful
3. Ensure no panics on errors

**Code Changes:**

In `pkg/analyzer/psaEvaluator_test.go`:
```go
var _ = Describe("Error Handling", func() {
    Context("File operations", func() {
        It("should handle non-existent file", func() {
            client := analyzer.NewClient("/nonexistent/file.yaml", "baseline")
            response, err := client.AnalyzeFile()
            Expect(err).To(HaveOccurred())
            Expect(err.Error()).To(ContainSubstring("no such file"))
        })

        It("should handle empty file", func() {
            // Create empty temp file
            tmpfile := createTempFile("")
            defer os.Remove(tmpfile)

            client := analyzer.NewClient(tmpfile, "baseline")
            response, err := client.AnalyzeFile()
            // Should handle gracefully
        })

        It("should handle permission denied", func() {
            // Create file without read permissions
            tmpfile := createTempFile("test")
            os.Chmod(tmpfile, 0000)
            defer os.Remove(tmpfile)

            client := analyzer.NewClient(tmpfile, "baseline")
            response, err := client.AnalyzeFile()
            Expect(err).To(HaveOccurred())
            Expect(err.Error()).To(ContainSubstring("permission denied"))
        })
    })

    Context("YAML parsing", func() {
        It("should handle malformed YAML", func() {
            yamlContent := []byte("{ malformed: [yaml")
            evaluator := analyzer.NewPsaEvaluator()
            response, err := evaluator.Evaluate(yamlContent, "baseline")
            Expect(err).To(HaveOccurred())
        })

        It("should handle non-K8s YAML", func() {
            yamlContent := []byte("foo: bar\nbaz: qux")
            evaluator := analyzer.NewPsaEvaluator()
            response, err := evaluator.Evaluate(yamlContent, "baseline")
            // Should skip non-K8s objects
        })
    })

    Context("Invalid parameters", func() {
        It("should reject invalid PSS level", func() {
            evaluator := analyzer.NewPsaEvaluator()
            yamlContent := []byte(validPodYAML)
            response, err := evaluator.Evaluate(yamlContent, "invalid-level")
            Expect(err).To(HaveOccurred())
            Expect(err.Error()).To(ContainSubstring("invalid"))
        })

        It("should reject invalid PSS version", func() {
            evaluator := analyzer.NewPsaEvaluator()
            yamlContent := []byte(validPodYAML)
            response, err := evaluator.Evaluate(yamlContent, "baseline", "v99.99")
            Expect(err).To(HaveOccurred())
        })
    })
})
```

---

## 5. Performance Improvements

### 5.1 Parallel Evaluation of Multi-Document Files

**Why:** Large files with many Kubernetes objects (like cluster dumps or Helm charts) could be processed faster by evaluating objects in parallel.

**How to Implement:**
1. Use goroutines to evaluate multiple objects concurrently
2. Use worker pool pattern to control concurrency
3. Aggregate results thread-safely

**Code Changes:**

In `pkg/analyzer/psaEvaluator.go`:
```go
import "sync"

func (e *psaEvaluator) Evaluate(stream []byte, levelString string) (AnalyzerResponse, error) {
    // ... existing setup code ...

    type evalJob struct {
        obj     runtime.Object
        gKV     *schema.GroupVersionKind
        content []byte
    }

    type evalResult struct {
        allowed bool
        result  ObjectResult
        err     error
    }

    jobs := make(chan evalJob, 100)
    results := make(chan evalResult, 100)

    // Worker pool
    var wg sync.WaitGroup
    numWorkers := runtime.NumCPU()

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                allowed, err := e.evaluate(job.obj, job.gKV, levelVersion)
                results <- evalResult{
                    allowed: allowed,
                    err:     err,
                }
            }
        }()
    }

    // Read and queue jobs
    go func() {
        for {
            // ... YAML parsing loop ...
            jobs <- evalJob{obj: obj, gKV: gKV, content: content}
        }
        close(jobs)
    }()

    // Collect results
    go func() {
        wg.Wait()
        close(results)
    }()

    var response AnalyzerResponse
    response.Allowed = true

    for result := range results {
        if result.err != nil {
            return response, result.err
        }
        response.Allowed = response.Allowed && result.allowed
        response.Results = append(response.Results, result.result)
    }

    return response, nil
}
```

**Testing:**
- **Benchmark:** Compare performance with/without parallelization

```go
func BenchmarkEvaluateSequential(b *testing.B) {
    evaluator := analyzer.NewPsaEvaluator(false) // parallel=false
    yamlContent := generateMultiDocYAML(1000)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = evaluator.Evaluate(yamlContent, "baseline")
    }
}

func BenchmarkEvaluateParallel(b *testing.B) {
    evaluator := analyzer.NewPsaEvaluator(true) // parallel=true
    yamlContent := generateMultiDocYAML(1000)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = evaluator.Evaluate(yamlContent, "baseline")
    }
}
```

---

### 5.2 Caching of Evaluator Instances

**Why:** Creating new evaluator instances has overhead. Reuse them across evaluations.

**How to Implement:**
1. Cache policy evaluator instances
2. Use sync.Pool for resource reuse
3. Benchmark to verify improvement

**Code Changes:**

```go
import "sync"

var evaluatorPool = sync.Pool{
    New: func() interface{} {
        eval, _ := policy.NewEvaluator(policy.DefaultChecks(), nil)
        return eval
    },
}

func (e *psaEvaluator) evaluate(obj runtime.Object, gKV *schema.GroupVersionKind, levelVersion api.LevelVersion) (bool, error) {
    // Get evaluator from pool
    evaluator := evaluatorPool.Get().(*policy.Evaluator)
    defer evaluatorPool.Put(evaluator)

    // ... rest of evaluation logic ...
}
```

**Testing:**
- **Benchmark:** Measure improvement

```go
func BenchmarkWithCaching(b *testing.B) {
    // Benchmark implementation with caching
}

func BenchmarkWithoutCaching(b *testing.B) {
    // Benchmark implementation without caching
}
```

---

### 5.3 Streaming Processing for Very Large Files

**Why:** Loading entire large files into memory can cause high memory usage. Stream processing reduces memory footprint.

**How to Implement:**
1. Use streaming YAML decoder
2. Process objects as they're decoded
3. Don't load entire file into memory

**Code Changes:**

```go
func (s *client) AnalyzeFile() (AnalyzerResponse, error) {
    var file *os.File
    var err error

    if s.filepath != "" && s.filepath != "-" {
        file, err = os.Open(s.filepath)
        if err != nil {
            return response, err
        }
        defer file.Close()
    } else {
        file = os.Stdin
    }

    // Pass reader instead of []byte
    evaluator := NewPsaEvaluator()
    response, err := evaluator.EvaluateStream(file, s.level)

    return response, err
}

// New method that takes io.Reader
func (e *psaEvaluator) EvaluateStream(reader io.Reader, levelString string) (AnalyzerResponse, error) {
    yamlDecoder := yaml.NewDecoder(reader)

    // Process incrementally
    for {
        var node yaml.Node
        err := yamlDecoder.Decode(&node)
        if errors.Is(err, io.EOF) {
            break
        }
        // Process node immediately without storing all
    }
}
```

**Testing:**
- **Unit Test:** Verify streaming works correctly
- **Benchmark:** Compare memory usage

```go
func BenchmarkMemoryUsageLargeFile(b *testing.B) {
    // Generate 100MB YAML file
    largeFile := generateLargeYAMLFile(100 * 1024 * 1024)

    b.ResetTimer()
    b.Run("Streaming", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            evaluator.EvaluateStream(largeFile, "baseline")
        }
    })

    b.Run("LoadAll", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            content, _ := os.ReadFile(largeFile)
            evaluator.Evaluate(content, "baseline")
        }
    })
}
```

---

## 6. Documentation Improvements

### 6.1 CI/CD Platform Examples

**Why:** Users want copy-paste examples for their specific CI/CD platforms.

**How to Implement:**
1. Create `docs/ci-examples/` directory
2. Add examples for popular platforms
3. Link from main README

**Files to Create:**

`docs/ci-examples/github-actions.md`:
```markdown
# GitHub Actions Examples

## Basic Check

\`\`\`yaml
name: PSS Check
on: [push, pull_request]
jobs:
  check-pss:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v3
        with:
          go-version: '1.21'
      - run: go install github.com/vicenteherrera/psa-checker@latest
      - run: psa-checker -f k8s/*.yaml -l restricted
\`\`\`

## With Helm Chart

\`\`\`yaml
# ... (full example)
\`\`\`
```

`docs/ci-examples/gitlab-ci.md`:
```markdown
# GitLab CI Examples

\`\`\`yaml
pss-check:
  image: golang:1.21
  stage: test
  script:
    - go install github.com/vicenteherrera/psa-checker@latest
    - helm template ./chart | psa-checker -f - -l baseline
\`\`\`
```

Similar files for:
- `jenkins.md`
- `azure-pipelines.md`
- `circleci.md`
- `bitbucket-pipelines.md`

**Testing:**
Actually test each example in the respective platform

---

### 6.2 Troubleshooting Guide

**Why:** Users encounter common issues that need documented solutions.

**How to Implement:**
Create `docs/troubleshooting.md` with common issues and solutions

**File Content:**

```markdown
# Troubleshooting Guide

## Common Issues

### "Empty input stream" error when using stdin

**Problem:** Getting error "empty input stream" when piping to psa-checker

**Solution:** Ensure the upstream command produces output:
\`\`\`bash
# Check if Helm actually produces output
helm template mychart | tee /tmp/output.yaml | psa-checker -f - -l baseline
\`\`\`

### "Non standard k8s node found" messages

**Problem:** Seeing many "Non standard k8s node found" messages

**Cause:** Your YAML contains non-Kubernetes objects or unsupported API versions

**Solution:** This is usually OK - the tool skips unknown objects. Use `--quiet` to suppress messages.

### Exit code 1 even though objects look compliant

**Problem:** Tool returns exit code 1 but violations aren't clear

**Solution:** Use verbose mode to see detailed check results:
\`\`\`bash
psa-checker -f manifest.yaml -l restricted --verbose
\`\`\`

### Helm chart evaluation fails with CRDs

**Problem:** Custom Resource Definitions cause evaluation errors

**Solution:** CRDs themselves don't create pods. Use `--api-version-handling skip` (default) to skip them.

## Performance Issues

### Slow evaluation of large files

**Problem:** Taking long time to evaluate large Helm charts

**Solutions:**
1. Use `--break` flag to stop on first error
2. Split evaluation of different namespaces
3. Filter out irrelevant namespaces with `--exclude-namespace`

### Out of memory errors

**Problem:** Process runs out of memory with very large files

**Solution:** Process in chunks:
\`\`\`bash
kubectl get pods -A -oyaml | yq '.items[] | split_doc' | psa-checker -f - -l baseline
\`\`\`

## Integration Issues

### GitHub Actions fails silently

**Problem:** Action completes but doesn't report results

**Solution:** Ensure you're checking exit code:
\`\`\`yaml
- run: psa-checker -f manifests/ -l baseline
  # Will fail step if non-compliant
\`\`\`

## Getting Help

If you encounter issues not covered here:
1. Check existing [GitHub Issues](https://github.com/vicenteherrera/psa-checker/issues)
2. Run with `--debug` flag and include output in your issue
3. Provide minimal reproduction case
```

---

### 6.3 Detailed Error Messages and Remediation

**Why:** Users need to understand WHY checks failed and HOW to fix them.

**How to Implement:**
1. Create mapping of check failures to remediation advice
2. Include in error output
3. Add `--explain` flag for detailed explanations

**Code Changes:**

Create `pkg/analyzer/remediation.go`:
```go
package analyzer

var remediationAdvice = map[string]string{
    "allowPrivilegeEscalation": `
Remediation: Add to container securityContext:
  securityContext:
    allowPrivilegeEscalation: false

Why: Prevents a container from gaining more privileges than its parent process.
`,
    "unrestricted capabilities": `
Remediation: Drop all capabilities:
  securityContext:
    capabilities:
      drop:
        - ALL
      add:
        - NET_BIND_SERVICE  # Only add specific capabilities needed

Why: Capabilities give containers subsets of root privileges. Dropping ALL is most secure.
`,
    "runAsNonRoot": `
Remediation: Run as non-root user:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000  # Use specific non-root UID

Why: Running as root increases blast radius if container is compromised.
`,
    // ... more mappings
}

func getRemediation(check string) string {
    if advice, ok := remediationAdvice[check]; ok {
        return advice
    }
    return "No specific remediation advice available for this check."
}
```

Update output to include remediation:
```go
if !results[i].Allowed {
    fmt.Printf("    Check %v failed: %v\n", i, results[i].ForbiddenReason)
    fmt.Printf("      %v\n", results[i].ForbiddenDetail)

    if showRemediation {
        fmt.Printf("      Remediation:\n%v\n", getRemediation(i))
    }
}
```

**Testing:**
- Verify remediation advice is shown for common failures
- Test that following advice actually fixes issues

---

## 7. Security & Operations

### 7.1 Generate SBOM (Software Bill of Materials)

**Why:** Security best practice for supply chain security. Enables:
- Vulnerability tracking
- License compliance
- Dependency auditing

**How to Implement:**
1. Use tools like `syft` or `go mod` to generate SBOM
2. Add to release process
3. Publish with releases

**Code Changes:**

Add to `.goreleaser.yml`:
```yaml
sboms:
  - artifacts: binary
    documents:
      - "${artifact}.spdx.json"
```

Add to `makefile`:
```makefile
.PHONY: sbom
sbom:
	@echo "Generating SBOM..."
	syft packages . -o spdx-json > psa-checker-sbom.json
	syft packages . -o cyclonedx-json > psa-checker-bom.json
	@echo "SBOM generated: psa-checker-sbom.json, psa-checker-bom.json"
```

Add to `.github/workflows/release.yaml`:
```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    path: ./
    artifact-name: sbom.spdx.json
```

**Testing:**
- Verify SBOM is generated correctly
- Validate SBOM format with validation tools

```bash
# Generate and validate
make sbom
sbom-tool validate psa-checker-sbom.json
```

---

### 7.2 Sign Releases

**Why:** Users can verify authenticity and integrity of downloaded binaries. Prevents supply chain attacks.

**How to Implement:**
1. Use `cosign` or GPG to sign releases
2. Sign container images
3. Document verification process

**Code Changes:**

Update `.goreleaser.yml`:
```yaml
signs:
  - cmd: cosign
    env:
      - COSIGN_EXPERIMENTAL=1
    certificate: '${artifact}.pem'
    args:
      - sign-blob
      - '--output-certificate=${certificate}'
      - '--output-signature=${signature}'
      - '${artifact}'
      - "--yes"
    artifacts: all
    output: true
```

Add verification docs to README:
```markdown
## Verifying Releases

### Binary Signatures

All releases are signed with cosign. To verify:

\`\`\`bash
# Download binary and signature
curl -LO https://github.com/vicenteherrera/psa-checker/releases/download/v0.0.6/psa-checker_linux_amd64
curl -LO https://github.com/vicenteherrera/psa-checker/releases/download/v0.0.6/psa-checker_linux_amd64.sig

# Verify
cosign verify-blob \
  --certificate psa-checker_linux_amd64.pem \
  --signature psa-checker_linux_amd64.sig \
  psa-checker_linux_amd64
\`\`\`

### Container Image Signatures

\`\`\`bash
cosign verify quay.io/vicenteherrera/psa-checker:v0.0.6
\`\`\`
```

**Testing:**
- Manually verify signatures work
- Add verification step to installation docs

---

### 7.3 Vulnerability Scanning in CI/CD

**Why:** Catch vulnerabilities in dependencies before release.

**How to Implement:**
1. Add Snyk, Trivy, or Grype to CI/CD
2. Scan both code and container images
3. Fail builds on high severity issues

**Code Changes:**

Create `.github/workflows/security-scan.yaml`:
```yaml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  scan-dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  scan-image:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build container image
        run: make container-build

      - name: Scan container image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'psa-checker:latest'
          format: 'sarif'
          output: 'trivy-image-results.sarif'

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-image-results.sarif'
```

Add to makefile:
```makefile
.PHONY: security-scan
security-scan:
	@echo "Scanning for vulnerabilities..."
	trivy fs --severity HIGH,CRITICAL .
	@echo "Scanning Go dependencies..."
	govulncheck ./...
```

**Testing:**
- Verify scans run successfully
- Test that high severity findings fail the build
- Ensure false positives can be suppressed

---

### 7.4 Metrics and Observability

**Why:** For production use and monitoring. Track:
- Usage patterns
- Performance metrics
- Error rates
- Most common violations

**How to Implement:**
1. Add optional telemetry flag
2. Export metrics in Prometheus format
3. Create dashboard templates

**Code Changes:**

```go
// Add metrics collection
import "github.com/prometheus/client_golang/prometheus"

var (
    evaluationsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "psa_checker_evaluations_total",
            Help: "Total number of PSS evaluations",
        },
        []string{"level", "allowed"},
    )

    objectsEvaluated = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "psa_checker_objects_evaluated_total",
            Help: "Total number of objects evaluated",
        },
        []string{"kind"},
    )

    checkFailures = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "psa_checker_check_failures_total",
            Help: "Total number of check failures",
        },
        []string{"check"},
    )

    evaluationDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "psa_checker_evaluation_duration_seconds",
            Help: "Time spent evaluating",
        },
        []string{"level"},
    )
)

func init() {
    prometheus.MustRegister(evaluationsTotal)
    prometheus.MustRegister(objectsEvaluated)
    prometheus.MustRegister(checkFailures)
    prometheus.MustRegister(evaluationDuration)
}

// Add to root.go
rootCmd.Flags().String("metrics-addr", "", "Address to expose Prometheus metrics (e.g., :9090)")
```

**Testing:**
- Verify metrics are exposed correctly
- Test Prometheus can scrape metrics
- Create sample Grafana dashboard

---

## Summary

This document outlines 30+ potential improvements organized into 7 categories:

1. **Critical Bug Fixes** (3 tasks) - Foundation improvements for stability
2. **Existing TODOs** (4 tasks) - Complete planned features
3. **User Experience** (7 tasks) - Make tool more user-friendly and capable
4. **Testing** (5 tasks) - Improve test coverage and quality assurance
5. **Performance** (3 tasks) - Optimize for speed and resource usage
6. **Documentation** (3 tasks) - Help users succeed with the tool
7. **Security & Operations** (4 tasks) - Production-readiness and supply chain security

## Prioritization Recommendation

### High Priority (Do First):
1. Replace panic() with proper error handling (1.1)
2. Configurable PSS version (2.1)
3. JSON output format (3.1)
4. Summary statistics (3.3)
5. Error path testing (4.5)

### Medium Priority (Do Next):
1. Structured logging (1.3)
2. Break-on-first-error (2.2)
3. Verbose/debug output (2.3)
4. Multiple file support (3.5)
5. Benchmark tests (4.1)
6. CI/CD examples (6.1)
7. SBOM generation (7.1)

### Lower Priority (Nice to Have):
1. SARIF output (3.2)
2. Namespace filtering (3.6)
3. Parallel evaluation (5.1)
4. Fuzz testing (4.2)
5. Vulnerability scanning (7.3)

### Future Enhancements:
1. Exit code options (3.7)
2. Output to file (3.4)
3. Streaming processing (5.3)
4. Metrics/observability (7.4)

Each task includes implementation guidance and testing strategies to ensure quality. Start with high-priority items that provide the most value to users while improving code quality and stability.
