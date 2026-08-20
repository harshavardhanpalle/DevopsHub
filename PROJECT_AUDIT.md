# PROJECT_AUDIT.md — devops-blog → DevOpsHub

Audit date: 2026-08-20
Source repo (as provided): `devops-blog__2_.zip`
Reference docs: `ArunCG-STK-26-1227-three-tier-app` (SipSugy PDF, architectural reference only — not to be copied verbatim), assignment instructions (DevOpsHub microservices spec)

## 1. Current Architecture

A single-service **static website** deployed as one container:

```
Developer → GitHub → Jenkins → Docker Build → Docker Hub →
Terraform Apply → EC2 (Docker run) → Nginx → static HTML
```

No backend, no database, no API layer, no microservices exist today. The
entire app is Nginx serving static files.

## 2. Current Frontend Structure

`website/` — plain HTML/CSS/JS, no build step, no framework, no bundler:

- `index.html` — home page, hardcoded "Latest Posts" cards (no data source)
- `blog.html` — "All Posts" list, hardcoded article cards
- `about.html` — static about content
- `contact.html` — a `<form id="contact-form">` handled **entirely client-side**
  in `script.js` (`preventDefault`, shows a canned "thanks" message, no
  network request — explicitly documented in the file as "no backend wired up")
- `styles.css` — 328 lines, single stylesheet, CSS custom properties (`--text-dim`
  etc.), used by all four pages
- `script.js` — 33 lines: mobile nav toggle, active-link highlighting, and the
  fake contact-form submit handler described above

There is **no JavaScript API client, no fetch/XHR calls, no article IDs,
slugs, or category taxonomy** anywhere in the code — articles are static
markup, not data. Every nav link (`index.html`, `about.html`, `blog.html`,
`contact.html`) is a real, working relative link between the four pages.

## 3. Current Backend Structure

None. There is no `backend/`, `api/`, `server/` directory and no server-side
language runtime in the repo.

## 4. Current Database Situation

None. No database, ORM, schema, or migration files exist.

## 5. Existing Docker Configuration

- `Dockerfile` — single stage, `nginx:alpine`, copies `nginx.conf` +
  `website/` into the image, exposes port 80, has a `HEALTHCHECK` using
  `wget` against `/`.
- `docker-compose.yml` — one service (`devops-blog`), builds from the root
  `Dockerfile`, maps `80:80`, has a matching `healthcheck` block.
- `nginx.conf` — single `server {}` block on port 80, gzip, cache headers for
  static assets, SPA-style fallback (`try_files … /index.html`) even though
  this isn't an SPA, 404 → `index.html`.

No multi-service networking, no service-name-based communication, no
API-gateway/reverse-proxy routing to other services exists yet — everything
this needs (routing `/api/*` to microservices, container-to-container
service names, per-service Dockerfiles) has to be added from scratch.

## 6. Existing Deployment Configuration

`infra/` — Terraform, AWS provider `~> 5.0`, deploys the **current
single-container static site** to a single EC2 instance:

- `provider.tf` — AWS provider, region var, commented-out optional S3 backend
- `main.tf` — root module wiring four child modules together
- `variables.tf` — project name, VPC/subnet CIDRs, AZ, instance type, key
  pair name, SSH CIDR, Docker Hub image, Elastic IP toggle, optional S3 toggle
- `modules/vpc/`, `modules/security_group/`, `modules/ec2/`, `modules/s3/` —
  each with their own `main.tf` / `variables.tf` / `outputs.tf`
- `terraform.tfvars` — environment-specific values (present in the zip; needs
  a check for committed secrets/account-specific values before reuse)

This is an **EC2 + Docker-run architecture**, not ECS/Fargate. It does not
provision ECR, ECS, ALB, RDS, SQS, or IAM roles for a multi-service app. The
DevOpsHub target architecture is materially different (containers on ECS
Fargate behind an ALB, RDS Postgres, SQS), so this Terraform will need new
modules (ecr, ecs, alb, rds, sqs, iam) rather than incremental edits to the
existing ec2 module. The existing vpc/security_group modules are the closest
to reusable, but will need additional subnets (public+private, multi-AZ) and
security groups (ALB↔ECS↔RDS) beyond what they currently define.

## 7. Existing CI/CD Configuration

`Jenkinsfile` — declarative pipeline, single Docker image, Docker Hub (not
ECR), stages: checkout → build image → push to Docker Hub → terraform
init/validate/plan/apply → read EC2 IP from Terraform output → SSH deploy
(`docker run` over SSH) → curl health check. This entire deploy mechanism
(SSH + `docker run` on a single EC2 host) is incompatible with the target
ECR → ECS Fargate → ALB flow and will need to be replaced, not patched.

## 8. Files That Should Be Preserved

- `website/*.html`, `website/styles.css` — design, branding, layout, copy
- `website/script.js` — nav toggle + active-link logic (contact-form handler
  will need to change once a real backend endpoint exists, but the toggle/nav
  logic stays)
- `infra/modules/vpc/`, `infra/modules/security_group/` — reusable as a
  starting point for the new networking layer, extended rather than replaced
- Overall visual identity ("OpsNotes" branding, badges, card layout) — no
  redesign, per instructions

## 9. Files That Need Modification

- `script.js` — wire the contact form (and, later, login/article fetches) to
  real API endpoints once the gateway exists, instead of the fake local
  handler
- `blog.html` / `index.html` — article cards are currently hardcoded HTML;
  these need to start rendering from `/api/articles` data instead (this is
  the main frontend/backend integration point — Phase 6, not now)
- `docker-compose.yml` — rebuild entirely to add the 4 microservices, Postgres,
  gateway/routing layer, and a local SQS-compatible component, while keeping
  the existing frontend service definition as its base
- `infra/main.tf`, `infra/variables.tf` — extend with ECR/ECS/ALB/RDS/SQS/IAM
  modules; existing EC2-based deploy path is superseded by ECS Fargate
- `Jenkinsfile` — replace the Docker Hub + SSH-to-EC2 deploy stages with
  ECR push + ECS service update stages

## 10. Files That Need Creation

- `user-service/`, `blog-service/`, `category-service/`, `notification-service/`
  — each: FastAPI app, Dockerfile, requirements.txt, models, routes,
  `/health` endpoint, tests
- `gateway/` (or equivalent) — single public entry point routing
  `/api/auth/*`, `/api/users/*`, `/api/articles/*`, `/api/categories/*`,
  `/api/notifications/*` to the right service by Docker service name
- PostgreSQL init/migrations per service (separate logical databases/schemas
  per the stated table ownership: users, articles, categories, notifications)
- Local SQS-compatible dev component (e.g. ElasticMQ or goaws) + wiring
- `.env.example`
- `tests/` per service
- `infra/modules/ecr/`, `infra/modules/ecs/`, `infra/modules/alb/`,
  `infra/modules/rds/`, `infra/modules/sqs/`, `infra/modules/iam/`
- `IMPLEMENTATION_STATUS.md` (created alongside this audit, see repo root)

## 11. Potential Problems

- **No backend exists at all** — this is a from-scratch build of 4 services,
  not a refactor. Scope is large; the assignment itself flags this and
  mandates a phased approach.
- **Terraform target architecture is a replacement, not an extension** —
  EC2+Docker-run vs. ECS Fargate+ALB+RDS are different deploy models. Reusing
  `vpc`/`security_group` is reasonable; the `ec2` and `s3` modules are not
  part of the target design.
- **Jenkinsfile deploy mechanism (SSH + `docker run`) must be fully replaced**
  with ECR/ECS-aware stages — not an incremental patch.
- **Frontend currently has zero data-fetching code** — connecting `blog.html`
  to `/api/articles` is a real (if small) frontend change, which the
  instructions permit ("only modify the frontend where necessary to connect
  it to the backend").
- **This sandboxed environment has no outbound network access** — I can
  write and unit-test code, and validate file structure, but I cannot
  actually run `docker compose up`, `terraform plan` against AWS, `pip
  install` from PyPI, or push to ECR/GitHub from here. Any "verified" claim
  in later phases will need to say explicitly what was and wasn't actually
  executed, per the assignment's own "do not claim PASS unless actually
  tested" rule.
- Need to confirm `infra/terraform.tfvars` doesn't contain anything sensitive
  before it's reused/extended (not inspected in detail yet beyond structure).

## 12. Recommended Implementation Sequence

Following the assignment's mandated phase order exactly:

1. **Phase 1 (this document)** — repository audit — **done**
2. **Phase 2** — scaffold the 4 FastAPI microservices (user, blog, category,
   notification), each with models, routes, `/health`, password hashing/JWT
   for user-service
3. **Phase 3** — Postgres schema/migrations per service
4. **Phase 4** — gateway/routing layer (single public entry point)
5. **Phase 5** — SQS notification flow (local dev substitute + production SQS)
6. **Phase 6** — frontend integration (fetch articles/categories, wire login,
   wire contact/notifications) without redesigning the site
7. **Phase 7** — rebuild `docker-compose.yml` for the full multi-service stack
8. **Phase 8** — tests + local verification (as far as this sandbox allows;
   flagged honestly where it can't run)
9. **Phase 9** — Terraform: new ecr/ecs/alb/rds/sqs/iam modules
10. **Phase 10** — Jenkinsfile rewrite for ECR/ECS
11. **Phase 11** — AWS deployment guidance (not executed from here — no AWS
    credentials or network access in this environment)

Recommended immediate next step: **Phase 2 — scaffold user-service first**
(other services depend on its auth pattern), then blog-service and
category-service together (they share the article/category relationship),
then notification-service last (it depends on the SQS plumbing from Phase 5
being decided).
