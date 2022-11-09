# Pod Security Admission command line checker

This command line tool statically checks for _Pod Security Standards_ levels on local YAML manifests or helm templates.

## Motivation

The Pod Security Admission included in Kubernetes 1.23 as beta enabled by default, checks pod's specs against [Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) of _privileged_, _baseline_ or _restricted_. It works perfectly fine doing its job to prevent pods non compliant with a namespace's PSS to run.

But it gives no warning when you deploy objects that creates pods but are not pods themselves: **Deployment, Daemonset, Replicaset, StatefulSet, Job or Cronjob**, unless you wait for them to create pods and watch logs.

There is also no tool to statically check files for those levels, without having a full cluster deployed... until now.

Pod Security Standards are the replacement for the deprecated Pod Security Policies (PSP) that are removed on Kubernetes v1.25.

## Warning

This project is in _alpha_ stage, how it handles input and output can change in several ways in the near future.

## How it works

This projects uses the [Pod Security Admission](https://github.com/kubernetes/pod-security-admission) library from Kubernetes repository to build a command line CLI you can use to check Kubernetes YAML manifests locally or in a pipeline.

The input manifest file can have any number of Kubernetes objects, all will be evaluated, and those that the check doesn't apply will be skipped.

This tool can't check into CRD that in turn creates pods, like when Tekton creates a pod to execute each step in a pipeline.


### Example

```console
$ # Check if a kubernetes file is compliant with PSS level "restricted"
$ psa-check deployment.yaml --test restricted
Deployment nginx-deployment
  PSS level restricted
    Check 8 failed: allowPrivilegeEscalation != false
      container "nginx" must set securityContext.allowPrivilegeEscalation=false
    Check 9 failed: unrestricted capabilities
      container "nginx" must set securityContext.capabilities.drop=["ALL"]
    Check 11 failed: runAsNonRoot != true
      pod or container "nginx" must set securityContext.runAsNonRoot=true
    Check 13 failed: seccompProfile
      pod or container "nginx" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost"
```

### Usage

```bash
# Check if a kubernetes file is compliant with PSS level "restricted"
psa-check -f deployment.yaml --level restricted

# Check if a kubernetes file is compliant with PSS level "baseline"
psa-check -f deployment.yaml --level baseline

# You can process a Helm chart from stdin
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm template prometheus-community/kube-prometheus-stack | psa-checker --level restricted -f -

# See all parameters
psa-check --help
```

### Installation

```bash
go install github.com/vicenteherrera/psa-checker@latest
```

### Build the binary

To build and test the binary on `release/psa-checker` use:

```bash
make 
```

## Artifact Hub Helm Charts

Using the script in util/hub_eval, you can evaluate all Helm charts published in Artifact Hub for compliance against PSS levels.
A future update will try to do a continuous evaluation of all charts.

Evaluation done on 2022-11-03 shows:

![Artifact Hub Helm charts PSS levels](./docs/ah_pss.png)

Category | Charts | Percentage
--- | --- | ----
Total | 9,830 | 100.00%
Privileged* | 782 | 7.96%
Baseline* | 5,437 | 55.31%
Restricted* | 38 | 0.39%
Error_download | 407 | 4.14%
Error_template | 610 | 6.21%
Empty_no_object | 533 | 5.42%
No_pod_object_but_crd | 1,313 | 13.36%
No_pod_object_no_crd | 187 | 1.90%
Version_not_evaluable | 523 | 5.32%

Legend:
* Privileged, Baseline, Restricted: doesn't account CRDs that could create pods
* Error_download: Downloading the template from original source wasn't possible
* Error_template: Rendering the template without providing parameters resulted in error
* No_pod_object_but_crd: The chart didn't render any object that can create pods, but has CRD that could do so
* No_pod_object_no_crd: The chart didn't render any object that can create pods nor CRDs
* Version_not_evaluable: The cart includes deployment, daemonset, etc. of v1beta1 that can't be evaluated by the library

