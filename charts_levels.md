[Go to root documentation](https://vicenteherrera.com/psa-checker)

## Artifact Hub's Helm charts evaluation

Source: [Artifact Hub](https://artifacthub.io/)  
Evaluation date: 2022-11-13, 10:27:38

### Pod Security Standards (PSS)

[Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) define three levels of security (restricted, baseline and privileged) that can be enforced for pods in a namespace. Evaluation done with [psa-checker](https://vicenteherrera.com/psa-checker/) command line tool, that checks into Kubernetes objects that can create pods.

| Category | Quantity | Percentage |
|------|------|------|
| Total | 9886 | 100.0% |
| Privileged | 786 | 7.95% |
| Baseline | 5458 | 55.21% |
| Restricted | 39 | 0.39% |
| Error_download | 408 | 4.13% |
| Error_template | 609 | 6.16% |
| Empty_no_object | 564 | 5.71% |
| No_pod_object_but_crd | 1313 | 13.28% |
| No_pod_object | 187 | 1.89% |
| Version_not_evaluable | 522 | 5.28% |

Legend:
 * PSS level:
   * Privileged: Pod specs makes use of privileged settings, the most insecure. Containers are able to access host capabilities.
   * Baseline: Pod specs without extra security or extra privileges. Doesn't account for CRD that may create pods.
   * Restricted: Pod specs follow the best security practices, like requiring containers to not run as root, and drop extra capabilities. Doesn't account for CRDs that may create pods.
 * Error_download: Downloading the template from original source wasn't possible.
 * Error_template: Rendering the template without providing parameters resulted in error.
 * No_pod_object_but_crd: The chart didn't render any object that can create pods, but has CRD that could do so.
 * No_pod_object_no_crd: The chart didn't render any object that can create pods nor CRDs.
 * Version_not_evaluable: The cart includes deployment, daemonset, etc. of v1beta1 that can't be evaluated by the library.

### Operator evaluation with BadRobot score

[BadRobot](https://github.com/controlplaneio/badrobot) evaluates how secure Kubernetes operators are. For each operator included in a chart, a score is calculated with a set of security practices. The closer to zero the score, the better.

| Score | Number of charts |
|------|------|
| Non-evaluable | 544 |
| No workload | 1520 |
| [0, -50) | 5630 |
| [-50, -100) | 993 |
| [-100, -150) | 105 |
| [-150, -200) | 26 |
| [-200, -250) | 14 |
| [-250, -300) | 7 |
| [-300, -350) | 2 |
| [-350, -400) | 1 |
| [-400, -450) | 1 |
| [-450, -500) | 0 |
| [-500, -550) | 1 |
| [-550, -600) | 0 |
| [-600, -650) | 0 |
| [-650, -700) | 1 |

### Charts list

Alphabetical list of all repositories (number of charts in parenthesis):

[main](./charts_levels)&nbsp; [A(1400)](./charts_levels_a)&nbsp; [B(472)](./charts_levels_b)&nbsp; [C(1001)](./charts_levels_c)&nbsp; [D(417)](./charts_levels_d)&nbsp; [E(221)](./charts_levels_e)&nbsp; [F(269)](./charts_levels_f)&nbsp; [G(328)](./charts_levels_g)&nbsp; [H(236)](./charts_levels_h)&nbsp; [I(206)](./charts_levels_i)&nbsp; [J(178)](./charts_levels_j)&nbsp; [K(632)](./charts_levels_k)&nbsp; [L(221)](./charts_levels_l)&nbsp; [M(399)](./charts_levels_m)&nbsp; [N(201)](./charts_levels_n)&nbsp; [O(476)](./charts_levels_o)&nbsp; [P(467)](./charts_levels_p)&nbsp; [Q(13)](./charts_levels_q)&nbsp; [R(356)](./charts_levels_r)&nbsp; [S(826)](./charts_levels_s)&nbsp; [T(961)](./charts_levels_t)&nbsp; [U(37)](./charts_levels_u)&nbsp; [V(98)](./charts_levels_v)&nbsp; [W(385)](./charts_levels_w)&nbsp; [X(1)](./charts_levels_x)&nbsp; [Y(56)](./charts_levels_y)&nbsp; [Z(29)](./charts_levels_z)&nbsp; 