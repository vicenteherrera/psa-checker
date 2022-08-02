package analyzer

import (
	"fmt"
	ioutils "io/ioutil"

	log "github.com/sirupsen/logrus"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/kubernetes/scheme"
	api "k8s.io/pod-security-admission/api"
	policy "k8s.io/pod-security-admission/policy"
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

	// Processing
	log.Info("Analyzing " + s.filepath)

	// Read pod
	decode := scheme.Codecs.UniversalDeserializer().Decode
	stream, _ := ioutils.ReadFile(s.filepath)
	obj, gKV, _ := decode(stream, nil, nil)
	if gKV.Kind != "Pod" {
		response.AnalysisStatus = "error"
		return response, nil
	}
	pod := obj.(*corev1.Pod)
	podMetadata := pod.ObjectMeta
	podSpec := pod.Spec
	//podMetadata, podSpec, err := api.PodSpecExtractor.ExtractPodSpec(pod)

	// Set up evaluator

	evaluator, _ := policy.NewEvaluator(policy.DefaultChecks())

	latest, _ := api.ParseVersion("latest")
	lv := api.LevelVersion{
		Level:   api.LevelRestricted,
		Version: latest,
	}

	// Evaluate
	results := evaluator.EvaluatePod(lv, &podMetadata, &podSpec)
	fmt.Printf("PSS level %v\n", lv.Level)
	for i := range results {
		if !results[i].Allowed {
			fmt.Printf("Check: %v\n", i)
			fmt.Printf("  Allowed: %v\n", results[i].Allowed)
			fmt.Printf("  ForbiddenReason: %v\n", results[i].ForbiddenReason)
			fmt.Printf("  ForbiddenDetail: %v\n", results[i].ForbiddenDetail)
		}
	}

	response.AnalysisStatus = "analyzed"
	log.Info(s.filepath + " : " + response.AnalysisStatus)

	return response, nil
}
