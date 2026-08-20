# DevOps Blog — Terraform + Docker + Jenkins on AWS

> **⚠️ Documentation notice (added during consolidation, 2026-08-20):**
> The prose and diagrams below describe the **original Stage 1 architecture**
> (single static site, one EC2 instance, Docker Hub, SSH deploy). The actual
> code in this repository has since moved to the **Stage 2/3 architecture**:
> 4 FastAPI microservices + an nginx gateway + a static frontend, all behind
> an Application Load Balancer on ECS Fargate, with Postgres/SQS via RDS/SQS,
> deployed through the `Jenkinsfile`'s GitHub → Jenkins → ECR → ECS pipeline.
> This README was never rewritten to match that (a real gap carried over
> from the source material, not something invented here) — treat
> `PROJECT_AUDIT.md` and `IMPLEMENTATION_STATUS.md` as the accurate,
> current description of the system, and the **Repository Structure**
> section just below as accurate (it has been updated to match this
> consolidated layout). Everything else in this file, including the
> "Run Locally with Docker Compose" instructions further down, refers to the
> old single-container setup and should not be relied on as-is.

End-to-end automated deployment of a containerized static DevOps blog on AWS.
Infrastructure is provisioned with **Terraform**, the site is packaged with
**Docker** (Nginx), and releases are automated with a **Jenkins** declarative
pipeline that goes from a GitHub push to a live EC2-hosted website.

## Architecture

```text
Developer → GitHub → Webhook → Jenkins → Docker Build → Docker Hub →
Terraform Apply → EC2 Deployment → Health Check → Live Website
```

```text
User Browser
     │
     ▼
Public IP (EC2, Elastic IP optional)
     │
     ▼
Nginx (Docker Container)
     │
     ▼
Static DevOps Blog Website
```

## Repository Structure

*(updated during consolidation to reflect what's actually in this repo — see notice above)*

```text
devops-blog/
├── frontend/                  # Static site (HTML/CSS/JS) + its own Dockerfile/nginx.conf
│   ├── website/
│   ├── Dockerfile
│   └── nginx.conf
├── nginx/                     # API gateway — routes /api/* to the 4 services by name
│   ├── Dockerfile
│   └── nginx.conf
├── services/
│   ├── user-service/          # FastAPI, auth/JWT, its own Dockerfile + tests
│   ├── blog-service/          # FastAPI, articles
│   ├── category-service/      # FastAPI, categories
│   └── notification-service/  # FastAPI, SQS consumer
├── infrastructure/
│   └── terraform/             # AWS provider v5+, modularized (vpc, security_group,
│       ├── provider.tf        # ecr, sqs, rds, iam, ecs_cluster, alb, ecs_service)
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars
│       ├── terraform.tfvars.example
│       └── modules/
├── scripts/
│   ├── db-init/                # per-service Postgres DB creation on first boot
│   └── local-sqs/               # ElasticMQ config for local SQS-compatible dev
├── docker-compose.yml          # local 8-container dev stack
├── Jenkinsfile                 # GitHub → Jenkins → tests → ECR → ECS deploy
├── README.md
├── IMPLEMENTATION_STATUS.md
├── PROJECT_AUDIT.md
├── .gitignore
└── .env.example
```

## Prerequisites

- AWS account with programmatic access (Access Key ID / Secret)
- An existing EC2 key pair in your target region (for SSH)
- Docker Hub account
- Jenkins server with: Docker, Terraform CLI, AWS CLI, `sshagent` plugin,
  and credentials configured (see below)
- Terraform >= 1.5.0

## 1. Run Locally with Docker Compose

```bash
docker compose up --build
# Site available at http://localhost
```

Or with plain Docker:

```bash
docker build -t devops-blog:local .
docker run -d -p 80:80 devops-blog:local
curl http://localhost
```

## 2. Provision Infrastructure with Terraform

The Terraform config is split into reusable modules (`modules/vpc`,
`modules/security_group`, `modules/ec2`, `modules/s3`). The root `main.tf`
just wires them together, so each concern can be modified, tested, or reused
independently.

```bash
cd infra
terraform init
terraform validate
terraform plan
terraform apply -auto-approve
```

Update `infra/terraform.tfvars` first with:
- `key_pair_name` — your existing AWS EC2 key pair name
- `ssh_allowed_cidr` — restrict to your IP (e.g. `203.0.113.10/32`)
- `docker_image` — your Docker Hub image, e.g. `youruser/devops-blog:latest`

Terraform outputs the public IP / URL:

```bash
terraform output website_url
```

## 3. Jenkins CI/CD Pipeline

> Updated for Stage 3: the app is now 6 containers (frontend, gateway,
> user-service, blog-service, category-service, notification-service)
> deployed to ECS Fargate behind an ALB (see Stage 2 `infra/`), not a
> single EC2 instance. The Docker Hub + SSH-to-EC2 pipeline described in
> earlier revisions of this doc no longer applies; the sections above
> (Architecture diagram, Repository Structure, Prerequisites) still
> describe the original single-container/EC2 design and are not
> updated as part of Stage 3 (out of scope — see IMPLEMENTATION_STATUS.md).

The `Jenkinsfile` implements a declarative pipeline with these stages:

1. Checkout code from GitHub
2. Validate required project files are present
3. Run each Python microservice's pytest suite (SQLite-backed, no external DB needed)
4. Build the 6 Docker images (frontend, gateway, and the 4 microservices)
5. Authenticate to Amazon ECR
6. Tag each image with the git commit SHA + Jenkins build number, push to ECR
7. Register a new ECS task definition revision per service (image tag only)
8. Update each ECS service (`--force-new-deployment`)
9. Wait for the ECS services to reach a stable state
10. Health check the live site through the ALB (`terraform output alb_dns_name`)

### Required Jenkins Credentials

| Credential ID           | Type                  | Purpose                          |
| ------------------------ | --------------------- | --------------------------------- |
| `aws-credentials`        | AWS Credentials (or username/password) | ECR login/push, ECS task-def register + service update |

### Required Jenkins Environment Variables

| Variable              | Purpose                                              |
| ---------------------- | ----------------------------------------------------- |
| `AWS_ACCOUNT_ID`       | 12-digit AWS account ID that owns the ECR repos/ECS cluster |
| `AWS_DEFAULT_REGION`   | Must match `infra/terraform.tfvars` `aws_region` (`ap-south-1`) |

No placeholder secret values are stored in the `Jenkinsfile` itself — both
of the above are read from Jenkins credentials/environment configuration at
runtime.

### GitHub Webhook

In your GitHub repo: **Settings → Webhooks → Add webhook**
- Payload URL: `http://<jenkins-server>/github-webhook/`
- Content type: `application/json`
- Trigger: **Just the push event**

In Jenkins job config, enable **GitHub hook trigger for GITScm polling**.

## 4. Verification

After a successful pipeline run:

```bash
# On the EC2 instance (or via SSH)
docker ps

# From anywhere
curl http://<EC2_PUBLIC_IP>
```

You should see the `devops-blog` container running and the homepage HTML
returned by `curl`.

## Notes

- The Terraform S3 bucket resource is optional (`create_s3_bucket = false`
  by default) — enable it in `terraform.tfvars` if you want a bucket for
  static assets or backups.
- The Elastic IP is enabled by default so the public IP doesn't change on
  instance stop/start; disable via `create_elastic_ip = false` if not needed.
- Tighten `ssh_allowed_cidr` before using this in anything beyond a demo —
  `0.0.0.0/0` is open to the world by default for convenience.
- Contact form on the site is client-side only; wire it to a real backend
  (API Gateway + Lambda, form service, etc.) if you need actual submissions.
