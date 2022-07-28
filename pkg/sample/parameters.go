package sample

import (
	log "github.com/sirupsen/logrus"
	"github.com/spf13/viper"
)

func ShowParams() {
	log.Info("Parameters used for invocation:")
	log.Info("filename: " + viper.GetString("filename"))
	log.Info("test: " + viper.GetString("test"))
	log.Info("break: " + viper.GetString("break"))
}
