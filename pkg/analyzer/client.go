package analyzer

import (
	ioutils "io/ioutil"
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
	evaluator := NewPsaEvaluator()
	response, err = evaluator.Evaluate(stream, s.level)

	return response, err
}
