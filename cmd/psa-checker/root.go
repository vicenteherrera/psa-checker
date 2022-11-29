package cmd

import (
	"errors"
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	analyzer "github.com/vicenteherrera/psa-checker/pkg/analyzer"
)

var cfgFile string

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:     "psa-checker",
	Version: version,
	Short:   "A CLI to check PSS levels as PSA will do",
	Long: `This is a CLI to check PSS levels as PSA will do.
	
For more information on how to use it, execute:
psa-checker help`,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	RunE: func(cmd *cobra.Command, args []string) error {
		var exitCode int

		filename := viper.GetViper().GetString("filename")
		level := viper.GetViper().GetString("level")

		if filename == "" {
			return errors.New("filename parameter is required")
		}

		// fmt.Fprintln(os.Stderr, "filename:", filename)

		// Main processing
		client := analyzer.NewClient(filename, level)
		response, _ := client.AnalyzeFile()
		if response.Allowed {
			fmt.Fprintln(os.Stderr, "Manifest(s) comply with PSS level "+level)
			exitCode = 0
		} else {
			fmt.Fprintln(os.Stderr, "Manifest(s) do not comply with PSS level "+level)
			exitCode = 1
		}
		os.Exit(exitCode)

		return nil
	},
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	cobra.OnInitialize(initConfig)

	// Here you will define your flags and configuration settings.
	// Cobra supports persistent flags, which, if defined here,
	// will be global for your application.

	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.test.yaml)")

	// Cobra local flags, which will only run when this action is called directly.

	rootCmd.Flags().StringP("filename", "f", "", "Name of the file to test")
	rootCmd.Flags().StringP("level", "l", "baseline", "Pod Security Standard level to test")
	// rootCmd.Flags().BoolP("break", "b", false, "Break on first error")

	viper.BindPFlag("filename", rootCmd.Flags().Lookup("filename"))
	viper.BindPFlag("level", rootCmd.Flags().Lookup("level"))

	// rootCmd.MarkFlagRequired("filename")

}

// initConfig reads in config file and ENV variables if set.
func initConfig() {
	if cfgFile != "" {
		// Use config file from the flag.
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory.
		// home, err := os.UserHomeDir()
		// cobra.CheckErr(err)

		// // Search config in home directory with name ".starter-go" (without extension).
		// viper.AddConfigPath(home)
		// viper.SetConfigType("yaml")
		// viper.SetConfigName(".starter-go")

		// Search current folder for config.yaml
		viper.AddConfigPath("./")
		viper.SetConfigType("yaml")
		viper.SetConfigName("config")
	}

	viper.AutomaticEnv() // read in environment variables that match

	// If a config file is found, read it in.
	if err := viper.ReadInConfig(); err == nil {
		fmt.Fprintln(os.Stderr, "Using config file:", viper.ConfigFileUsed())
	}

}
