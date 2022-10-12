package analyzer_test

import (
	"os"
	"testing"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/vicenteherrera/psa-checker/pkg/analyzer"
)

func TestGenerator(t *testing.T) {
	RegisterFailHandler(Fail)
	RunSpecs(t, "Generator Suite")
}

var psaEvaluator analyzer.PsaEvaluator
var err error
var unrelatedYaml []byte
var podYamlBaseline, podYamlRestricted, podYamlPrivileged []byte

func loadTestFiles() {
	//TODO: feal pod level manifests
	podYamlBaseline, err = os.ReadFile("../../test/pod-baseline.yaml")
	if err != nil {
		panic(err)
	}
	podYamlRestricted, err = os.ReadFile("../../test/pod-restricted.yaml")
	if err != nil {
		panic(err)
	}
	podYamlPrivileged, err = os.ReadFile("../../test/pod-privileged.yaml")
	if err != nil {
		panic(err)
	}
	unrelatedYaml, err = os.ReadFile("../../test/serviceaccount.yaml")
	if err != nil {
		panic(err)
	}
}

var _ = BeforeSuite(func() {
	psaEvaluator = analyzer.NewPsaEvaluator()
	loadTestFiles()
})

var _ = Describe("PsaEvaluator", func() {

	Context("When I analize an unrelated manifest", func() {
		It("It doesn't return an error", func() {
			// _, _ = fmt.Fprintf(GinkgoWriter, "manifest:\n%s", unrelatedYaml)
			_, err := psaEvaluator.Evaluate(unrelatedYaml, "baseline")
			Expect(err).ShouldNot(HaveOccurred())
		})
	})
	Context("When I analize an pod manifest", func() {
		Context("for baseline pod", func() {
			It("It doesn't return an error", func() {
				// _, _ = fmt.Fprintf(GinkgoWriter, "manifest:\n%s", podYamlBaseline)
				_, err := psaEvaluator.Evaluate(podYamlBaseline, "baseline")
				Expect(err).ShouldNot(HaveOccurred())
			})
		})
		Context("for privielged pod", func() {
			It("It doesn't return an error", func() {
				// _, _ = fmt.Fprintf(GinkgoWriter, "manifest:\n%s", podYamlPrivileged)
				_, err := psaEvaluator.Evaluate(podYamlPrivileged, "baseline")
				Expect(err).ShouldNot(HaveOccurred())
			})
		})
		Context("for restricted pod", func() {
			It("It doesn't return an error", func() {
				// _, _ = fmt.Fprintf(GinkgoWriter, "manifest:\n%s", podYamlRestricted)
				_, err := psaEvaluator.Evaluate(podYamlRestricted, "baseline")
				Expect(err).ShouldNot(HaveOccurred())
			})
		})

	})

})
