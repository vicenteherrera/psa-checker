# starter-go application

This is a starter Go application with explanation of all steps to setup development environment, general libraries used, and best practices. Read the main `/README.md` on the repository for further information.

**This documentation doesn't reflect the current state of the application, but its intended usage once finished.**

## Porpoise

This little application reads Containerfile/Dockerfile files and Kubernetes specification YAML files and searches for bad practices, like:

* Containerfile/Dockerfile:
  * Not including the `USER` command, so the container runs as root
* Kubernetes YAML:
  * Specifying `priviliged: true` in a container security context

## Configuration

starter-go can accept parameters defined in a configuration file, from command line, or as enviroment variables.

It will automatically load a `config.yaml` file that is located on its own directory.
