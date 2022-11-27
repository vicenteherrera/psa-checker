package analyzer

import (
	"bufio"
	"errors"
	"fmt"
	"os"
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
	var stream []byte
	var input string
	var err error

	// Read file
	if s.filepath != "" && s.filepath != "-" {
		stream, err = os.ReadFile(s.filepath)
		if err != nil {
			response.AnalysisStatus = "error"
			return response, err
		}
	} else {
		fmt.Printf("Reading from stdinv\n")
		scanner := bufio.NewScanner(os.Stdin)
		for scanner.Scan() {
			input += scanner.Text() + "\n"
		}
		if scanner.Err() != nil {
			return response, scanner.Err()
		}
		stream = []byte(input)

		if len(stream) == 0 {
			return response, errors.New("Empty imput stream")
		}
	}

	// iterate yaml documents
	evaluator := NewPsaEvaluator()
	response, err = evaluator.Evaluate(stream, s.level)

	return response, err
}
