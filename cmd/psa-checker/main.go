package main

import (
	"errors"
	"fmt"
	"os"

	analyzer "github.com/vicenteherrera/psa-checker/pkg/analyzer"

	"github.com/spf13/pflag"
	"github.com/spf13/viper"
)

func main() {
	var exitCode int
	// Check for errors in configuration
	if err := configure(); err != nil {
		fmt.Printf("%s \n\n", err)
		pflag.Usage()
		os.Exit(1)
	}

	// Main processing
	client := analyzer.NewClient(viper.GetString("filename"), viper.GetString("level"))
	response, _ := client.AnalyzeFile()
	// response, err := client.AnalyzeFile()
	// if err != nil {
	// 	log.Error(err)
	// }
	if response.Allowed {
		exitCode = 0
	} else {
		exitCode = 1
	}
	os.Exit(exitCode)
}

func configure() error {

	// Activate getting env variables with viper.Get
	viper.AutomaticEnv()

	// Config file setup
	viper.SetConfigName("config")            // name of config file (without extension)
	viper.SetConfigType("yaml")              // REQUIRED if the config file does not have the extension in the name
	viper.AddConfigPath("$HOME/.starter-go") // call multiple times to add many search paths
	viper.AddConfigPath(".")                 // optionally look for config in the working directory
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			// Config file not found; ignored error
		} else {
			panic(fmt.Errorf("fatal error config file: %w", err))
		}
	}

	// Command line parameter setup (precedence over config file)
	pflag.StringP("filename", "f", "", "Name of the file to test")
	pflag.StringP("type", "t", "yaml", "File type")
	pflag.String("level", "baseline", "Pod Security Standard level to test")
	// pflag.BoolP("break", "b", false, "Break on first error")

	// TODO: Make filename required, or admit pipe strings, error on empty one, and on extra parameters

	// Bind all flags for viper.Get
	pflag.VisitAll(func(flag *pflag.Flag) { viper.BindPFlag(flag.Name, flag) })

	// Parse configuration
	pflag.Parse()

	// Validation of parameters
	if viper.GetString("filename") == "" {
		return errors.New("filename is required")
	}

	return nil
}
