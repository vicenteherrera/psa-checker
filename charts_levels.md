[Go to root documentation](https://vicenteherrera.com/psa-checker)

## Artifact Hub's Helm charts evaluation

Source: [Artifact Hub](https://artifacthub.io/)  
Evaluation date: 2022-11-23, 10:20:35

### Pod Security Standards (PSS)

[Pod Security Standards (PSS)](https://kubernetes.io/docs/concepts/security/pod-security-standards/) define three levels of security (restricted, baseline and privileged) that can be enforced for pods in a namespace. Evaluation done with [psa-checker](https://vicenteherrera.com/psa-checker/) command line tool, that checks into Kubernetes objects that can create pods.

| Category | Quantity | Percentage |
|------|------|------|
| Total | 10193 | 100.0% |
| Privileged | 551 | 5.41% |
| Baseline | 4323 | 42.41% |
| Restricted | 32 | 0.31% |
| Error_download | 2264 | 22.21% |
| Error_template | 751 | 7.37% |
| Empty_no_object | 377 | 3.7% |
| No_pod_object_but_crd | 1247 | 12.23% |
| Version_not_evaluable | 491 | 4.82% |
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
| Non-evaluable | 379 |
| No workload | 1399 |
| [0, -50) | 4063 |
| [-50, -100) | 200 |
| [-100, -150) | 64 |
| [-150, -200) | 14 |
| [-200, -250) | 9 |
| [-250, -300) | 5 |
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

[main](./charts_levels)&nbsp; [A(1414)](./charts_levels_a)&nbsp; [B(473)](./charts_levels_b)&nbsp; [C(1006)](./charts_levels_c)&nbsp; [D(421)](./charts_levels_d)&nbsp; [E(233)](./charts_levels_e)&nbsp; [F(270)](./charts_levels_f)&nbsp; [G(536)](./charts_levels_g)&nbsp; [H(240)](./charts_levels_h)&nbsp; [I(226)](./charts_levels_i)&nbsp; [J(180)](./charts_levels_j)&nbsp; [K(639)](./charts_levels_k)&nbsp; [L(222)](./charts_levels_l)&nbsp; [M(401)](./charts_levels_m)&nbsp; [N(203)](./charts_levels_n)&nbsp; [O(482)](./charts_levels_o)&nbsp; [P(473)](./charts_levels_p)&nbsp; [Q(13)](./charts_levels_q)&nbsp; [R(359)](./charts_levels_r)&nbsp; [S(824)](./charts_levels_s)&nbsp; [T(967)](./charts_levels_t)&nbsp; [U(37)](./charts_levels_u)&nbsp; [V(99)](./charts_levels_v)&nbsp; [W(387)](./charts_levels_w)&nbsp; [X(1)](./charts_levels_x)&nbsp; [Y(57)](./charts_levels_y)&nbsp; [Z(30)](./charts_levels_z)&nbsp; 