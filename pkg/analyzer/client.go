package analyzer

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	ioutils "io/ioutil"

	corev1 "k8s.io/api/core/v1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/kubectl/pkg/scheme"
	api "k8s.io/pod-security-admission/api"
	policy "k8s.io/pod-security-admission/policy"

	appsv1 "k8s.io/api/apps/v1"
	batchv1 "k8s.io/api/batch/v1"

	yaml "gopkg.in/yaml.v3"
)

// First declare all public methods of the class
type Client interface {
	AnalyzeFile() (AnalyzerResponse, error)
}

// New object
func NewClient(filepath string, level string) Client {
	return &client{
		filepath: filepath,
		level:    level,
	}
}

// Third private properties
type client struct { //lowercase first letter = private
	filepath string
	level    string
}

func (s *client) AnalyzeFile() (AnalyzerResponse, error) { //uppercase first letter = public

	var response AnalyzerResponse

	// Read file
	stream, err := ioutils.ReadFile(s.filepath)
	if err != nil {
		response.AnalysisStatus = "error"
		return response, err
	}

	response.Allowed = true

	// iterate yaml documents
	response, err = s.iterate(stream, s.level)

	return response, err
}

func (s *client) iterate(stream []byte, level string) (AnalyzerResponse, error) {
	var allowed bool
	var obj runtime.Object
	var gKV *schema.GroupVersionKind
	var err, err2 error
	var response AnalyzerResponse
	dec := yaml.NewDecoder(bytes.NewReader(stream))
	decode := scheme.Codecs.UniversalDeserializer().Decode
	latest, _ := api.ParseVersion("latest")
	olevel, _ := api.ParseLevel(level)
	levelVersion := api.LevelVersion{
		Level:   olevel,
		Version: latest,
	}

	for {
		var node yaml.Node
		err := dec.Decode(&node)
		if errors.Is(err, io.EOF) {
			break
		}
		if err != nil {
			panic(err)
		}

		content, err := yaml.Marshal(&node)
		if err != nil {
			panic(err)
		}

		// prepare yaml document for evaluation
		obj, gKV, err2 = decode(content, nil, nil)
		if err2 != nil {
			response.AnalysisStatus = "error"
			continue
		}

		//process response
		allowed, err = s.evaluate(obj, gKV, levelVersion)
		response.Allowed = response.Allowed && allowed
	}
	return response, err
}

func (s *client) evaluate(obj runtime.Object, gKV *schema.GroupVersionKind, levelVersion api.LevelVersion) (bool, error) {
	var podMetadata v1.ObjectMeta
	var podSpec corev1.PodSpec
	var name string
	evaluator, _ := policy.NewEvaluator(policy.DefaultChecks())

	switch gKV.Kind {
	case "Pod":
		pod := obj.(*corev1.Pod)
		name = pod.ObjectMeta.Name
		podMetadata = pod.ObjectMeta
		podSpec = pod.Spec
	case "Deployment":
		deployment := obj.(*appsv1.Deployment)
		name = deployment.ObjectMeta.Name
		podMetadata = deployment.ObjectMeta
		podSpec = deployment.Spec.Template.Spec
	case "DaemonSet":
		daemonset := obj.(*appsv1.DaemonSet)
		name = daemonset.ObjectMeta.Name
		podMetadata = daemonset.ObjectMeta
		podSpec = daemonset.Spec.Template.Spec
	case "ReplicaSet":
		replicaset := obj.(*appsv1.ReplicaSet)
		name = replicaset.ObjectMeta.Name
		podMetadata = replicaset.ObjectMeta
		podSpec = replicaset.Spec.Template.Spec
	case "Job":
		job := obj.(*batchv1.Job)
		name = job.ObjectMeta.Name
		podMetadata = job.ObjectMeta
		podSpec = job.Spec.Template.Spec
	case "CronJob":
		cronJob := obj.(*batchv1.CronJob)
		name = cronJob.ObjectMeta.Name
		podMetadata = cronJob.ObjectMeta
		podSpec = cronJob.Spec.JobTemplate.Spec.Template.Spec
	default:
		fmt.Printf("Kind not evaluable: %v\n", gKV.Kind)
		return true, nil
	}

	fmt.Printf("%v %v\n", gKV.Kind, name)

	// Evaluate
	allowed := true
	results := evaluator.EvaluatePod(levelVersion, &podMetadata, &podSpec)
	fmt.Printf("  PSS level %v %v\n", levelVersion.Level, levelVersion.Version)
	for i := range results {
		if !results[i].Allowed {
			fmt.Printf("    Check %v failed: %v\n", i, results[i].ForbiddenReason)
			fmt.Printf("      %v\n", results[i].ForbiddenDetail)
			allowed = false
		}
	}

	return allowed, nil
}
