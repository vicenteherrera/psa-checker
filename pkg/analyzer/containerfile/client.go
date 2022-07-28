package analyzer

import log "github.com/sirupsen/logrus"

// First declare all public methods of the class
type Client interface {
	AnalyzeFile() (AnalyzerResponse, error)
}

// Second object constructor implementation
func NewClient(filepath string) Client { //convention: New+Class name
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

	response.AnalysisStatus = "analyzed"

	log.Info(s.filepath + " : " + response.AnalysisStatus)

	return response, nil
}
