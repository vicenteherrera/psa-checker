package analyzer

import (
	"bytes"
	"errors"
	"fmt"
	"io"

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

type PsaEvaluator interface {
	Evaluate(stream []byte, level string) (AnalyzerResponse, error)
}

func NewPsaEvaluator() PsaEvaluator {
	return &psaEvaluator{}
}

type psaEvaluator struct {
}

func (e *psaEvaluator) Evaluate(stream []byte, levelString string) (AnalyzerResponse, error) {
	var allowed bool
	var obj runtime.Object
	var gKV *schema.GroupVersionKind
	var err error
	var response AnalyzerResponse
	var latest api.Version
	var level api.Level

	yamlDecoder := yaml.NewDecoder(bytes.NewReader(stream))
	k8sDecode := scheme.Codecs.UniversalDeserializer().Decode
	response.Allowed = true

	//TODO: Accept PSS version as a parameter
	latest, err = api.ParseVersion("latest")
	if err != nil {
		panic(err)
	}
	level, err = api.ParseLevel(levelString)
	if err != nil {
		panic(err)
	}

	levelVersion := api.LevelVersion{
		Level:   level,
		Version: latest,
	}

	for {
		var node yaml.Node
		err = yamlDecoder.Decode(&node)
		if errors.Is(err, io.EOF) {
			response.AnalysisStatus = "eof"
			break
		}
		if err != nil {
			response.AnalysisStatus = "error"
			panic(err)
		}

		content, err := yaml.Marshal(&node)
		if err != nil {
			response.AnalysisStatus = "error"
			panic(err)
		}

		// prepare yaml document for evaluation
		obj, gKV, err = k8sDecode(content, nil, nil)
		if err != nil {
			fmt.Printf("Non standard k8s node found\n")
			response.AnalysisStatus = "error"
			//TODO: Take into consideration break parameter flag
			continue
		}

		//process response
		allowed, err = e.evaluate(obj, gKV, levelVersion)
		if err != nil {
			response.AnalysisStatus = "error"
			panic(err)
		}
		response.Allowed = response.Allowed && allowed
	}

	if response.AnalysisStatus == "error" {
		return response, err
	}

	return response, nil
}

func (e *psaEvaluator) evaluate(obj runtime.Object, gKV *schema.GroupVersionKind, levelVersion api.LevelVersion) (bool, error) {
	var podMetadata v1.ObjectMeta
	var podSpec corev1.PodSpec
	var name string
	evaluator, _ := policy.NewEvaluator(policy.DefaultChecks())

	// TODO: Defer return true or false after whole document evaluation depending on configuration
	// f.e.: You may want to consider that including non evaluable versions should render the level as privileged
	// or you may just skip them depending on command line parameters

	switch gKV.Kind {
	case "Pod":
		pod := obj.(*corev1.Pod)
		name = pod.ObjectMeta.Name
		podMetadata = pod.ObjectMeta
		podSpec = pod.Spec
	case "Deployment":
		if gKV.Group+gKV.Version != "appsv1" {
			fmt.Printf(gKV.Group+"."+gKV.Version+" not evaluable for kind: %v\n", gKV.Kind)
			return true, nil
		}
		deployment := obj.(*appsv1.Deployment)
		name = deployment.ObjectMeta.Name
		podMetadata = deployment.ObjectMeta
		podSpec = deployment.Spec.Template.Spec
	case "DaemonSet":
		if gKV.Group+gKV.Version != "appsv1" {
			fmt.Printf("Version "+gKV.Version+" not evaluable for kind: %v\n", gKV.Kind)
			return true, nil
		}
		daemonset := obj.(*appsv1.DaemonSet)
		name = daemonset.ObjectMeta.Name
		podMetadata = daemonset.ObjectMeta
		podSpec = daemonset.Spec.Template.Spec
	case "ReplicaSet":
		if gKV.Group+gKV.Version != "appsv1" {
			fmt.Printf("Version "+gKV.Version+" not evaluable for kind: %v\n", gKV.Kind)
			return true, nil
		}
		replicaset := obj.(*appsv1.ReplicaSet)
		name = replicaset.ObjectMeta.Name
		podMetadata = replicaset.ObjectMeta
		podSpec = replicaset.Spec.Template.Spec
	case "StatefulSet":
		if gKV.Group+gKV.Version != "appsv1" {
			fmt.Printf("Version "+gKV.Version+" not evaluable for kind: %v\n", gKV.Kind)
			return true, nil
		}
		statefulset := obj.(*appsv1.StatefulSet)
		name = statefulset.ObjectMeta.Name
		podMetadata = statefulset.ObjectMeta
		podSpec = statefulset.Spec.Template.Spec
	case "Job":
		if gKV.Group+gKV.Version != "batchv1" {
			fmt.Printf("Version "+gKV.Version+" not evaluable for kind: %v\n", gKV.Kind)
			return true, nil
		}
		job := obj.(*batchv1.Job)
		name = job.ObjectMeta.Name
		podMetadata = job.ObjectMeta
		podSpec = job.Spec.Template.Spec
	case "CronJob":
		if gKV.Group+gKV.Version != "batchv1" {
			fmt.Printf("Version "+gKV.Version+" not evaluable for kind: %v\n", gKV.Kind)
			return true, nil
		}
		cronJob := obj.(*batchv1.CronJob)
		name = cronJob.ObjectMeta.Name
		podMetadata = cronJob.ObjectMeta
		podSpec = cronJob.Spec.JobTemplate.Spec.Template.Spec
	default:
		//TODO: optional log message on verbose output
		fmt.Printf("Kind not evaluable: %v\n", gKV.Kind)
		return true, nil
	}

	fmt.Printf("%v %v\n", gKV.Kind, name)

	// Evaluate
	allowed := true
	results := evaluator.EvaluatePod(levelVersion, &podMetadata, &podSpec)
	//TODO: optional log message on verbose output
	fmt.Printf("  PSS level %v %v\n", levelVersion.Level, levelVersion.Version)
	for i := range results {
		if !results[i].Allowed {
			fmt.Printf("    Check %v failed: %v\n", i, results[i].ForbiddenReason)
			fmt.Printf("      %v\n", results[i].ForbiddenDetail)
			allowed = false
		}
	}

	//TODO: make error return error
	return allowed, nil
}
