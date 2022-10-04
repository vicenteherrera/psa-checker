package analyzer

import (
	"fmt"
	ioutils "io/ioutil"

	corev1 "k8s.io/api/core/v1"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/scheme"
	api "k8s.io/pod-security-admission/api"
	policy "k8s.io/pod-security-admission/policy"

	appsv1 "k8s.io/api/apps/v1"
)

// First declare all public methods of the class
type Client interface {
	AnalyzeFile() (AnalyzerResponse, error)
}

// New object
func NewClient(filepath string) Client {
	return &client{
		filepath: filepath,
	}
}

// Third private properties
type client struct { //lowercase first letter = private
	filepath string
}

// Last public methods implementation
func (s *client) AnalyzeFile() (AnalyzerResponse, error) { //uppercase first letter = public

	var response AnalyzerResponse
	var podMetadata v1.ObjectMeta
	var podSpec corev1.PodSpec

	// Processing

	// Read pod
	decode := scheme.Codecs.UniversalDeserializer().Decode
	stream, _ := ioutils.ReadFile(s.filepath)
	obj, gKV, _ := decode(stream, nil, nil)
	if gKV.Kind == "Pod" {

		pod := obj.(*corev1.Pod)
		podMetadata = pod.ObjectMeta
		podSpec = pod.Spec
		fmt.Printf("Pod %v\n", podMetadata.Name)
	} else if gKV.Kind == "Deployment" {
		deployment := obj.(*appsv1.Deployment)
		podMetadata = deployment.ObjectMeta
		podSpec = deployment.Spec.Template.Spec
		fmt.Printf("Deployment %v\n", podMetadata.Name)
	} else {
		response.AnalysisStatus = "error"
		return response, nil
	}

	// Set up evaluator

	evaluator, _ := policy.NewEvaluator(policy.DefaultChecks())

	latest, _ := api.ParseVersion("latest")
	lv := api.LevelVersion{
		Level:   api.LevelRestricted,
		Version: latest,
	}

	// Evaluate
	results := evaluator.EvaluatePod(lv, &podMetadata, &podSpec)
	fmt.Printf("  PSS level %v\n", lv.Level)
	for i := range results {
		if !results[i].Allowed {
			fmt.Printf("    Check %v failed: %v\n", i, results[i].ForbiddenReason)
			fmt.Printf("      %v\n", results[i].ForbiddenDetail)
		}
	}

	response.AnalysisStatus = "analyzed"

	return response, nil
}
