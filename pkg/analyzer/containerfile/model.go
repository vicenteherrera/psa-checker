package analyzer

import "time"

type AnalyzerResponse struct {
	AnalysisStatus string    `json:"analysis_status"`
	CreatedAt      time.Time `json:"created_at"`
	Allowed        bool      `json:"allowed"`
}
