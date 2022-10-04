# Pod Security Admission command line checker

This projects uses the Pod Security Admission library to build a command line CLI you can use to check Kubernetes YAML manifests locally or in a pipeline.

## How it works

The official Pod Security Admission on the Kubernetes project will only evaluate Pod manifests, so a Deployment, Daemonset, Job or Cronjob can be admited, while in fact its pod will never be allowed to run by the admission.

This checker does look into those kind of objects, so you can check if there is any problem on your files beforehand.

The input manifest file can have any number of Kubernetes objects, all will be evaluated.

## Example

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

## Usage

```bash
# Check if a kubernetes file is compliant with PSS level "restricted"
psa-check deployment.yaml --test restricted

# Check if a kubernetes file is compliant with PSS level "baseline"
psa-check deployment.yaml --test baseline

# Break on first error encountered
psa-check deployment.yaml --test baseline --break

# Help al see all parameters
psa-check --help
```

## Build the binary

To build the binary on `release/psa-checker` use:

```bash
make build
```





