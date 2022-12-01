[Go to root documentation](https://vicenteherrera.com/psa-checker)

## Artifact Hub's Helm charts evaluation

Source: [Artifact Hub](https://artifacthub.io/)  
Evaluation date: 2022-12-01, 09:47:41

### Pod Security Standards (PSS)

[Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) define three levels of security (restricted, baseline and privileged) that can be enforced for pods in a namespace. Evaluation done with [psa-checker](https://vicenteherrera.com/psa-checker/) command line tool, that checks into Kubernetes objects that can create pods.

| Category | Quantity | Percentage |
|------|------|------|
| Total | 10260 | 100.0% |
| Privileged | 553 | 5.39% |
| Baseline | 4329 | 42.19% |
| Restricted | 31 | 0.3% |
| Error_download | 314 | 3.06% |
| Error_template | 2539 | 24.75% |
| Empty_no_object | 595 | 5.8% |
| No_pod_object_but_crd | 1251 | 12.19% |
| Version_not_evaluable | 492 | 4.8% |
| No_pod_object | 156 | 1.52% |

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
| Non-evaluable | 567 |
| No workload | 1387 |
| [0, -50) | 4043 |
| [-50, -100) | 198 |
| [-100, -150) | 64 |
| [-150, -200) | 15 |
| [-200, -250) | 7 |
| [-250, -300) | 6 |
| [-300, -350) | 2 |
| [-350, -400) | 1 |
| [-400, -450) | 1 |
| [-450, -500) | 0 |
| [-500, -550) | 0 |
| [-550, -600) | 0 |
| [-600, -650) | 0 |
| [-650, -700) | 1 |

### Charts list

Alphabetical list of all repositories (number of charts in parenthesis):

[main](./charts_levels)&nbsp; [A(1416)](./charts_levels_a)&nbsp; [B(475)](./charts_levels_b)&nbsp; [C(1008)](./charts_levels_c)&nbsp; [D(423)](./charts_levels_d)&nbsp; [E(233)](./charts_levels_e)&nbsp; [F(271)](./charts_levels_f)&nbsp; [G(551)](./charts_levels_g)&nbsp; [H(242)](./charts_levels_h)&nbsp; [I(227)](./charts_levels_i)&nbsp; [J(180)](./charts_levels_j)&nbsp; [K(643)](./charts_levels_k)&nbsp; [L(228)](./charts_levels_l)&nbsp; [M(401)](./charts_levels_m)&nbsp; [N(203)](./charts_levels_n)&nbsp; [O(485)](./charts_levels_o)&nbsp; [P(475)](./charts_levels_p)&nbsp; [Q(14)](./charts_levels_q)&nbsp; [R(360)](./charts_levels_r)&nbsp; [S(835)](./charts_levels_s)&nbsp; [T(976)](./charts_levels_t)&nbsp; [U(37)](./charts_levels_u)&nbsp; [V(99)](./charts_levels_v)&nbsp; [W(388)](./charts_levels_w)&nbsp; [X(2)](./charts_levels_x)&nbsp; [Y(58)](./charts_levels_y)&nbsp; [Z(30)](./charts_levels_z)&nbsp; 