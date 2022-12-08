package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

// Based on: https://github.com/controlplaneio/badrobot/blob/master/cmd/version.go

var (
	// vars injected with ldflags at build time (this can be done automatically by goreleaser)
	version = "unknown"
	commit  = "unknown"
	date    = "unknown"
	builtBy = "Unknown"
)

func init() {
	rootCmd.AddCommand(versionCmd)
}

var versionCmd = &cobra.Command{
	Use:   `version`,
	Short: "Prints badrobot version",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("version %s, git commit %s, date %s, built by %s \n", version, commit, date, builtBy)
	},
}
