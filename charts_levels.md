[Go to root documentation](https://vicenteherrera.com/psa-checker)

## Artifact Hub's Helm charts evaluation

Source: [Artifact Hub](https://artifacthub.io/)  
Evaluation date: 2022-11-27, 21:51:50

### Pod Security Standards (PSS)

[Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) define three levels of security (restricted, baseline and privileged) that can be enforced for pods in a namespace. Evaluation done with [psa-checker](https://vicenteherrera.com/psa-checker/) command line tool, that checks into Kubernetes objects that can create pods.

| Category | Quantity | Percentage |
|------|------|------|
| Total | 10217 | 100.0% |
| Privileged | 552 | 5.4% |
| Baseline | 4324 | 42.32% |
| Restricted | 32 | 0.31% |
| Error_download | 2284 | 22.35% |
| Error_template | 751 | 7.35% |
| Empty_no_object | 375 | 3.67% |
| No_pod_object_but_crd | 1250 | 12.23% |
| Version_not_evaluable | 492 | 4.82% |
| No_pod_object | 157 | 1.54% |

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
| Non-evaluable | 380 |
| No workload | 1413 |
| [0, -50) | 4067 |
| [-50, -100) | 193 |
| [-100, -150) | 64 |
| [-150, -200) | 15 |
| [-200, -250) | 8 |
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

[main](./charts_levels)&nbsp; [A(1415)](./charts_levels_a)&nbsp; [B(474)](./charts_levels_b)&nbsp; [C(1008)](./charts_levels_c)&nbsp; [D(423)](./charts_levels_d)&nbsp; [E(233)](./charts_levels_e)&nbsp; [F(271)](./charts_levels_f)&nbsp; [G(536)](./charts_levels_g)&nbsp; [H(241)](./charts_levels_h)&nbsp; [I(226)](./charts_levels_i)&nbsp; [J(180)](./charts_levels_j)&nbsp; [K(642)](./charts_levels_k)&nbsp; [L(225)](./charts_levels_l)&nbsp; [M(401)](./charts_levels_m)&nbsp; [N(203)](./charts_levels_n)&nbsp; [O(483)](./charts_levels_o)&nbsp; [P(474)](./charts_levels_p)&nbsp; [Q(13)](./charts_levels_q)&nbsp; [R(359)](./charts_levels_r)&nbsp; [S(831)](./charts_levels_s)&nbsp; [T(967)](./charts_levels_t)&nbsp; [U(37)](./charts_levels_u)&nbsp; [V(99)](./charts_levels_v)&nbsp; [W(387)](./charts_levels_w)&nbsp; [X(1)](./charts_levels_x)&nbsp; [Y(58)](./charts_levels_y)&nbsp; [Z(30)](./charts_levels_z)&nbsp; 