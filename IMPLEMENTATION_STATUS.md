============================================================
CONSOLIDATION -- MERGE OF ALL UPLOADED ZIPS INTO devops-blog-final.zip
============================================================

CURRENT PHASE: Repository consolidation (post Stage 3). No application
code, Terraform resources, or CI/CD stages were rewritten, redesigned, or
invented in this pass -- this phase only merges 7 uploaded ZIPs into one
clean repository and reorganizes it into the requested folder layout.

INPUTS INSPECTED (7 uploaded ZIPs):
- files1.zip            -- PROJECT_AUDIT.md + IMPLEMENTATION_STATUS.md
                            (Stage 1, in-progress wording) + a nested
                            devopshub-stage1.zip (an early, slightly less
                            mature Stage 1 -- missing .gitignore's Python/.env
                            entries at repo root in this variant is not the
                            issue; rather its notification-service SQS
                            consumer lacked graceful shutdown + safe
                            retry-on-failure semantics, and user-service's
                            requirements.txt was missing bcrypt==4.0.1)
- files_copy.zip         -- PROJECT_AUDIT.md + an EARLIER draft of
                            IMPLEMENTATION_STATUS.md (Phase 1 only, written
                            before any service code existed) -- superseded
                            by every other source, not used
- devops-blog-main.zip   -- the ORIGINAL pre-audit repo (Stage 0): a single
                            static Nginx site, EC2 + Docker Hub Terraform/
                            Jenkins. This is the documented starting point
                            referenced in PROJECT_AUDIT.md section 1; its
                            website/ content was already carried forward
                            (with additions) into every later stage, so
                            nothing further was pulled from it directly
- devopshub-stage1-final.zip -- corrected Stage 1 (4 FastAPI microservices,
                            gateway, docker-compose, tests). Fixes the two
                            issues above and includes .env.example. Used as
                            the Stage 1 baseline.
- devopshub-stage2.zip   -- Stage 1-final + Terraform (vpc, security_group,
                            ecr, sqs, rds, iam, ecs_cluster, alb, ecs_service
                            modules). Its Jenkinsfile/README were still the
                            unmodified Stage 1 versions (Docker Hub + SSH) --
                            not used for those two files.
- devopshub-final.zip    -- Stage 2 + the real Stage 3 Jenkinsfile (ECR/ECS
                            pipeline, 331 lines) and an updated
                            IMPLEMENTATION_STATUS.md. Used as the primary
                            source for nearly everything in this repo.
- files__5_.zip           -- IMPLEMENTATION_STATUS.md (identical to the
                            files1.zip copy) + a nested devopshub-stage1-final.zip
                            that is byte-for-byte IDENTICAL to the top-level
                            devopshub-stage1-final.zip upload -- pure
                            duplicate, nothing unique taken from it.

MERGE DECISION: devopshub-final.zip's tree was used as the base for
everything (services, gateway, frontend, Terraform, Jenkinsfile, docker-
compose.yml), since it is the most complete, latest valid version per the
Stage 1 -> Stage 2 -> Stage 3 progression confirmed above. Two files were
pulled in from elsewhere because devopshub-final.zip was missing them:
- .env.example  <- devopshub-stage1-final.zip (present in Stage 1-final,
  silently dropped somewhere between Stage 1 and the Stage 2 zip; nothing
  in it is Stage-2/3-specific, so the Stage 1 copy is still correct)
- .gitignore    <- files1.zip's nested devopshub-stage1.zip (the ONLY
  source of any of the 7 that included a .gitignore at all; devopshub-final,
  devopshub-stage2, and devopshub-stage1-final all lack one at the repo
  root)

FOLDER REORGANIZATION (mechanical move, no code rewritten):
- website/ + root Dockerfile + root nginx.conf  -> frontend/
- gateway/                                       -> nginx/
- user-service/, blog-service/, category-service/,
  notification-service/                          -> services/<name>/
- infra/                                         -> infrastructure/terraform/
- db-init/, local-sqs/                           -> scripts/<name>/
Because this changes relative paths, docker-compose.yml build/volume paths
and the Jenkinsfile's TF_DIR, required-file list, per-service test `dir()`
calls, and Docker build contexts were updated to match (path strings only --
no stage/service logic changed). Terraform module `source = "./modules/..."`
paths are relative to infra/ itself, so moving the whole folder needed no
internal Terraform edits. Re-validated after the moves: docker-compose.yml
still parses as valid YAML; every .tf file's braces are still balanced;
every .py file still compiles; every .js file still passes `node --check`.

FILES CREATED: none (this phase reorganizes/merges existing files only)

FILES MODIFIED:
- docker-compose.yml -- 6 path references updated for the new folder layout
  (db-init, local-sqs, and 5 of 6 build contexts); no service definitions,
  env vars, healthchecks, or ports changed
- Jenkinsfile -- TF_DIR, the required-files check list, the per-service
  `dir()` test path, and the Docker Build context map updated for the new
  folder layout, plus matching comment-path updates; no stage was added,
  removed, or reordered, and no shell logic inside a stage changed
- README.md -- prepended a notice flagging that its prose/diagrams describe
  the old Stage 1 EC2 + Docker Hub design rather than the Stage 2/3 ECS
  Fargate design actually in this repo (a pre-existing gap in the source
  material, not introduced here -- see MISSING ITEMS below), and replaced
  the Repository Structure diagram with one that matches this consolidated
  layout. No other prose in README.md was rewritten.

FILES REMOVED: none from the final tree (the losing/duplicate ZIP contents
were simply not copied in; nothing was deleted out of a chosen source)

FILES PRESERVED AS-IS FROM devopshub-final.zip: all service app/ code,
Dockerfiles, requirements.txt, tests/, gateway nginx.conf, frontend website/
+ Dockerfile + nginx.conf, all Terraform files under modules/, PROJECT_AUDIT.md

DUPLICATES RESOLVED:
- files1.zip vs files_copy.zip vs files__5_.zip vs the 4 devopshub-*.zip
  uploads all overlap heavily (same PROJECT_AUDIT.md repeated 3x; the same
  devopshub-stage1-final.zip bytes uploaded twice, once directly and once
  nested inside files__5_.zip). Only one copy of each unique artifact was
  kept, per the newest/most-complete rule above.

NOT VERIFIED (see Stage 1/2/3 sections below for the original, unchanged
verification status of the application/infra logic itself -- this
consolidation pass re-ran only the lightweight syntax checks listed above;
it did NOT re-run pip install, pytest, docker build/up, or terraform
validate/plan, none of which are available in this sandboxed environment
either):
- Docker Compose `up`/`build`, `docker` is not installed here
- `terraform validate`/`plan`, `terraform` is not installed here
- pytest execution for any service, no outbound network access to pip
  install dependencies

MISSING ITEMS:
- assignment.pdf -- no assignment PDF was present in any of the 7 uploaded
  ZIPs, so none is included; this is reported rather than fabricated
- docs/ and a top-level tests/ folder were NOT created -- nothing in the
  uploads needs them (each service's tests/ is intentionally colocated
  with its own app/ and Dockerfile, per each test file's own docstring
  instructions to `cd <service> && pytest`; moving them to a shared
  top-level tests/ folder would break that documented workflow for no
  benefit), so per "do not create empty or unnecessary folders" they were
  left out
- README.md's body (architecture diagrams, prerequisites, "Run Locally"
  steps) still describes the Stage 1 EC2 + Docker Hub design, not the
  Stage 2/3 ECS Fargate design implemented in this repo -- this was never
  rewritten in any of the 7 uploaded ZIPs, and a full rewrite was
  intentionally not invented here; flagged in-file instead (see README.md
  notice)

EXACT NEXT STEP: none required for the consolidation itself -- this
repository is ready to be committed as-is. The one open item worth
prioritizing next is rewriting README.md's body to describe the actual
Stage 2/3 architecture, since the notice added here is a flag, not a fix.

============================================================
STAGE 3 -- JENKINS CI/CD + FINAL VERIFICATION
============================================================

CURRENT PHASE: Stage 3 -- Jenkins CI/CD only. No application code, no
Terraform (infra/*.tf), and no new AWS resources were added or redesigned.
The existing 6-service ECS Fargate architecture from Stage 2 is unchanged;
this stage only adds/replaces the automation that builds and deploys it.

COMPLETED:
- Rewrote Jenkinsfile: old pipeline built one image, pushed to Docker Hub,
  and SSH-deployed it to a single EC2 instance -- none of that target
  exists anymore after Stage 2 (EC2/S3 modules are dead code, replaced by
  ECS Fargate + ALB). New pipeline: checkout -> validate required files ->
  run each Python microservice's pytest suite -> build the 6 images the
  Stage 2 architecture actually deploys -> ECR login -> tag
  (git-commit-sha + build number) and push to the 6 existing ECR repos ->
  register a new ECS task definition revision per service (image bump
  only, all other task-def fields inherited from the Terraform-created
  revision) -> `ecs update-service --force-new-deployment` per service ->
  `aws ecs wait services-stable` -> health check the live site through
  the ALB (DNS read from `terraform output alb_dns_name`, not hardcoded).
- Updated README.md section 3 ("Jenkins CI/CD Pipeline") and its
  credentials table to describe the new pipeline instead of the removed
  Docker Hub/EC2-SSH one; added a note that the rest of the README
  (architecture diagram, repo structure, prerequisites) still describes
  the original Stage-1 single-container design and was left as-is
  (out of scope for this stage, see MINIMAL CHANGE RULE).

IN PROGRESS: none.

FILES CREATED: none.

FILES MODIFIED (2):
FILE: Jenkinsfile
ACTUAL PROBLEM: Every stage targeted infrastructure that no longer exists
  post-Stage-2 (Docker Hub image name/credentials, `terraform apply` run
  from inside the app pipeline, SSH to a single EC2 host, health check
  against an EC2 IP). It could not have deployed the current 6-service
  ECS architecture at all.
MINIMUM FIX: Full replacement of the pipeline's build/push/deploy stages
  (Docker Hub -> ECR, EC2 SSH -> ECS task-def update + service deploy,
  EC2-IP health check -> ALB-DNS health check) plus adding a test stage,
  since none of the old stages were reusable for the new target. Did NOT
  touch Terraform: this file assumes `infra/` has already been applied
  once and only updates container images/ECS services, per Stage 3 scope
  ("Terraform may be run only if genuinely required for deployment" -- it
  is not, here).

FILE: README.md
ACTUAL PROBLEM: Section 3 documented the removed Docker Hub/EC2-SSH
  pipeline and its credential IDs, which would mislead anyone configuring
  Jenkins for this repo.
MINIMUM FIX: Replaced section 3's stage list and credentials table with
  the actual new pipeline/credential ID; added one note flagging that
  earlier sections (architecture diagram, prerequisites) are still
  Stage-1-era and unchanged. No other section rewritten.

FILES DELETED: none.

---

JENKINS STATUS: Jenkinsfile rewritten for GitHub -> tests -> Docker build
(6 images) -> ECR -> ECS task-definition update -> ECS deploy ->
services-stable wait -> ALB health check. NOT VERIFIED -- no Jenkins
server, Docker daemon, AWS credentials, or network access in this
sandbox to actually run the pipeline (same environment constraint as
Stage 1/2; see NOT VERIFIED ITEMS). Groovy syntax was checked by hand and
brace/paren-balance-checked with a script (105/105 braces, 52/52 parens);
this is not a substitute for an actual Jenkins Pipeline Linter run.

ECR STATUS: Unchanged from Stage 2 (still NOT VERIFIED -- repos not yet
created, since `terraform apply` hasn't run in any real environment).
Jenkinsfile's push stage targets the 6 repo names Terraform will create
(`${project_name}-${service}`, matching infra/modules/ecr/main.tf exactly)
-- not independently verified end-to-end.

ECS DEPLOYMENT STATUS: NOT VERIFIED -- same reason (no cluster/services
exist yet in any real AWS account this sandbox can reach). Task-definition
family names, service names, and the frontend-only ALB target group the
Jenkinsfile references were cross-checked by hand against
infra/modules/ecs_service/main.tf, infra/modules/ecs_cluster/main.tf, and
infra/main.tf's 6 `ecs_service` module instantiations.

ALB STATUS: Unchanged from Stage 2 (NOT VERIFIED). Jenkinsfile's health
check reads `alb_dns_name` from `terraform output`, so it will only work
once Stage 2's `terraform apply` has actually run.

RDS STATUS: Unchanged from Stage 2 -- not touched this stage.

SQS STATUS: Unchanged from Stage 2 -- not touched this stage.

TESTS EXECUTED: user-service / blog-service / category-service /
notification-service pytest suites -- NOT RUN in this sandbox (no network
access to `pip install` each service's requirements.txt; same constraint
noted in every prior stage's status file). The Jenkinsfile's "Run Tests"
stage runs all four with a fresh venv per service and a SQLite
DATABASE_URL override, matching each test file's own documented
invocation (see e.g. user-service/tests/test_user_service.py's docstring).

TEST RESULTS: N/A -- nothing was executed in this stage.

VERIFIED ITEMS:
- Jenkinsfile Groovy brace/paren balance (script-checked).
- ECR repo naming, ECS cluster name, ECS service/task-family naming, and
  the ALB output name the Jenkinsfile references all cross-checked by
  hand against the actual Stage 2 Terraform (infra/modules/ecr/main.tf,
  infra/modules/ecs_cluster/main.tf, infra/modules/ecs_service/main.tf,
  infra/outputs.tf) -- they match exactly, so once `terraform apply` has
  run for real, the Jenkinsfile's hardcoded name-construction logic
  (`${PROJECT_NAME}-${service}`) will resolve to real resources without
  needing any AWS-side lookup/discovery step.
- Each Python microservice's test files confirmed to be self-contained
  (SQLite override, no external Postgres/SQS dependency), so the pytest
  stage doesn't need docker-compose's Postgres/local-sqs containers
  running.

NOT VERIFIED ITEMS (everything below requires a Jenkins server, Docker
daemon, real AWS credentials, and a previously-`apply`'d Stage 2 infra --
none available in this sandbox):
- Actually running the Jenkins pipeline end-to-end.
- pytest suites actually passing (only confirmed self-contained by
  reading them, not executed).
- Docker builds for all 6 images actually succeeding.
- ECR authentication, push, and image visibility in the console.
- ECS task-definition registration (the inline Python that patches the
  container image and strips read-only fields from `describe-task-definition`
  output) actually producing a valid `register-task-definition` payload
  against the real API.
- `ecs update-service --force-new-deployment` and `ecs wait
  services-stable` actually converging.
- ALB health check passing against a live target.
- Frontend navigation, API gateway routing, authentication, article
  APIs, category APIs, notification APIs, RDS connectivity, SQS
  notification flow -- none of these were re-verified this stage (would
  require a live deployment; app-level behavior itself was not changed).

KNOWN ISSUES:
- Everything under NOT VERIFIED ITEMS above.
- The rest of README.md (architecture diagram, repository structure,
  prerequisites) is still Stage-1-era and describes the old
  single-container/EC2 design; only section 3 (Jenkins) was corrected
  this stage, per the minimal-change rule -- a full README rewrite for
  the Stage 2/3 architecture would be a reasonable follow-up but is not
  a CI/CD or deployment-compatibility problem, so it wasn't done here.
- Jenkinsfile assumes `infra/` has already been `apply`'d once (ECR
  repos, ECS cluster/services, ALB, and their initial task-definition
  revisions must already exist) -- it registers new task-def *revisions*
  and updates existing services, it does not create them from scratch.
  This matches Stage 3's instruction scope (don't recreate AWS resources
  unnecessarily) but is worth stating explicitly as an operational
  precondition.
- No `sshagent`/EC2-specific Jenkins plugin dependency remains, but the
  new pipeline does require the Jenkins agent to have `aws` CLI, `docker`,
  `python3`, and `terraform` available on PATH (only `terraform` is used,
  read-only, for the final health-check's `terraform output`) -- not
  independently verified in a real Jenkins agent.

EXACT NEXT STEP:
1. Complete Stage 2's own EXACT NEXT STEP first (terraform init/validate/
   plan/apply against real AWS credentials) -- Stage 3's pipeline has
   nothing to push images into or deploy onto until that infra exists.
2. In a real Jenkins instance: install the Docker, AWS Credentials (or
   pipeline-aws), and Pipeline plugins; create the `aws-credentials`
   credential and the `AWS_ACCOUNT_ID` / `AWS_DEFAULT_REGION` environment
   variables documented at the top of the Jenkinsfile and in README.md
   section 3; point a pipeline job at this repo.
3. Run the pipeline once manually (not via webhook) and fix whatever a
   real Jenkins agent's Pipeline Linter / an actual `docker build` /
   `aws ecs register-task-definition` surfaces that this sandbox's
   manual review couldn't catch.
4. Once a run succeeds end-to-end, wire up the GitHub webhook (README.md
   section 3 already documents the payload URL/trigger) for push-based
   builds.

============================================================
STAGE 2 RECORD (unchanged below -- Stage 3 did not modify infra/)
============================================================

CURRENT PHASE: Stage 2 -- AWS infrastructure + Terraform only. Application
code (user-service, blog-service, category-service, notification-service,
gateway, frontend, tests, docker-compose.yml) was NOT touched -- see FILES
MODIFIED below, which is infra/ + this file only. Jenkins/CI-CD is
explicitly out of scope for this stage and was not started.

STAGE 2 STATUS: Terraform written and internally reviewed. NOT deployed --
no AWS credentials/network access in this sandbox (confirmed: no `terraform`
binary installed, no outbound network to install one or run
`terraform init`). See TERRAFORM STATUS / NOT VERIFIED ITEMS below.

---

FILES CREATED (22):
- infra/modules/ecr/{main,variables,outputs}.tf -- 6 ECR repos (frontend,
  gateway, user-service, blog-service, category-service,
  notification-service), image scanning on push, lifecycle policy (keep
  last 10 images)
- infra/modules/ecs_cluster/{main,variables,outputs}.tf -- Fargate/Fargate
  Spot ECS cluster, Container Insights, Cloud Map HTTP namespace
  (devopshub.local) for ECS Service Connect
- infra/modules/ecs_service/{main,variables,outputs}.tf -- reusable module
  (task definition + service + CloudWatch log group + Service Connect
  config), instantiated 6 times from infra/main.tf, one per
  docker-compose.yml service
- infra/modules/alb/{main,variables,outputs}.tf -- public ALB, HTTP:80
  listener, one target group (frontend, port 80, target_type "ip")
- infra/modules/rds/{main,variables,outputs}.tf -- single PostgreSQL 16
  instance in private subnets, generated master password + master
  credentials in Secrets Manager, plus 4 precomposed DATABASE_URL secrets
  (one per service database: userdb/blogdb/categorydb/notificationdb)
- infra/modules/sqs/{main,variables,outputs}.tf -- "devopshub-notifications"
  queue + "-dlq" dead-letter queue, redrive policy (maxReceiveCount=5),
  redrive_allow_policy restricting the DLQ to only the main queue
- infra/modules/iam/{main,variables,outputs}.tf -- shared ECS task
  execution role (ECR pull, CloudWatch Logs, Secrets Manager read scoped to
  this project's secrets only) + a second app task role (SQS
  Send/Receive/Delete/GetQueueAttributes/GetQueueUrl, scoped to exactly the
  notifications queue ARN), attached only to user-service, blog-service,
  notification-service
- infra/terraform.tfvars.example -- template with no secrets (RDS/JWT
  credentials are Terraform-generated into Secrets Manager, never variables)

FILES MODIFIED (11):
- infra/main.tf -- fully rewritten: wires vpc -> security_group -> ecr / sqs
  / rds -> iam -> ecs_cluster -> alb -> the 6 ecs_service modules. No longer
  instantiates the old ec2/ or s3/ modules (superseded architecture -- see
  PROJECT_AUDIT.md section 6/9). Those two module directories are left on
  disk, untouched, in case anyone wants the old EC2 path for reference; they
  are simply not called from root anymore.
- infra/variables.tf -- fully rewritten for the ECS/RDS/ALB/SQS variable
  set (region, project_name, VPC/subnet CIDRs, az_count,
  enable_nat_gateway, image_tag, task cpu/memory/desired_count, RDS sizing,
  SQS settings, jwt_expire_minutes). Old EC2-only variables
  (key_pair_name, docker_image, ssh_allowed_cidr, create_elastic_ip,
  instance_type, create_s3_bucket, s3_bucket_name) removed since nothing
  references them anymore.
- infra/outputs.tf -- fully rewritten: website_url (ALB DNS), ALB DNS name,
  VPC/subnet IDs, ECR repo URL map, ECS cluster name, RDS endpoint, RDS
  master-credentials secret ARN, SQS queue/DLQ URLs. Old EC2/S3 outputs
  removed.
- infra/provider.tf -- added the `random` provider (used by RDS/JWT secret
  generation) and bumped the aws provider constraint to
  ">= 5.40.0, < 6.0.0" (aws_ecs_service.service_connect_configuration
  requires >= 5.40). Backend-S3 comment block left as-is.
- infra/terraform.tfvars -- content replaced to match the new variables.tf
  (was EC2-only values for a "devops-blog" project name); no secrets were
  or are present in this file.
- infra/modules/vpc/{main,variables,outputs}.tf -- extended from a single
  public subnet/AZ to public+private subnets across 2 AZs, plus a NAT
  Gateway (single NAT, in AZ #1, to control cost) so private-subnet ECS
  tasks can reach ECR/SQS/CloudWatch. Outputs changed from singular
  `public_subnet_id` to `public_subnet_ids` / `private_subnet_ids` lists --
  this is why the old ec2 module (which expects a single `subnet_id`) is no
  longer wired from root; it would need its own small adapter to keep
  working, which wasn't worth doing for a module that's no longer part of
  the target architecture.
- infra/modules/security_group/{main,variables,outputs}.tf -- replaced the
  single "web" SG (80/443/22 open to the world) with three SGs: alb
  (80 from 0.0.0.0/0), ecs_tasks (80 from the ALB SG only + self-referencing
  rules for the other 5 container ports, for Service Connect traffic), and
  rds (5432 from the ecs_tasks SG only). No SSH ingress anywhere -- Fargate
  tasks aren't SSH'd into.

FILES DELETED: none. infra/modules/ec2/ and infra/modules/s3/ still exist on
disk exactly as before; they are just no longer referenced by infra/main.tf.

---

TERRAFORM STATUS: Written, not run. `terraform` is not installed in this
sandbox and there is no outbound network access to install it or reach the
Terraform Registry / AWS APIs (same environment constraint noted in
Stage 1's IMPLEMENTATION_STATUS.md). What WAS done instead, as a substitute
sanity check:
  - Every .tf file's brace `{}`/paren `()` counts were verified balanced
    (script-checked, all 36 files OK).
  - Every `module` block in infra/main.tf was cross-checked against its
    module's variables.tf to confirm every argument name it passes is a
    real declared variable (script-checked, all 8 root-level modules OK;
    the 6 ecs_service instantiations were checked by hand since their
    `environment =` / `secrets =` blocks are nested maps, not module
    arguments, which a naive script can't tell apart).
  - Manually re-read every module for resource attribute names/types
    against the AWS provider docs I have from training (e.g.
    aws_ecs_service.service_connect_configuration, aws_sqs_queue
    redrive_policy/redrive_allow_policy, aws_db_instance encryption/
    subnet-group args).
None of this is a substitute for `terraform validate`/`plan` against the
real provider schema. See NOT VERIFIED ITEMS.
- terraform fmt: NOT VERIFIED (no terraform binary)
- terraform validate: NOT VERIFIED (no terraform binary)
- terraform plan: NOT VERIFIED (no terraform binary, no AWS credentials)

VPC STATUS: Written, NOT VERIFIED. 1 VPC, 2 public subnets (ALB) + 2 private
subnets (ECS tasks + RDS) across 2 AZs (data-sourced via
aws_availability_zones, not hardcoded), 1 IGW, 1 NAT Gateway (single AZ, to
control cost -- documented tradeoff, same one the SipSugy reference doc
flags as a "known next step").

ECR STATUS: Written, NOT VERIFIED. 6 private repos, one per
docker-compose.yml service, scan-on-push enabled, lifecycle policy caps
each at the last 10 images. No images have been built or pushed -- this
stage is infra only, no CI/CD.

ECS STATUS: Written, NOT VERIFIED. 1 Fargate cluster (Container Insights
on), Cloud Map HTTP namespace `devopshub.local` for ECS Service Connect, 6
services (frontend, gateway, user-service, blog-service, category-service,
notification-service) each with their own task definition (256 CPU / 512 MB
by default, awsvpc network mode, private subnets, no public IP). Service
Connect discovery names exactly match the docker-compose.yml service names
(e.g. "gateway", "user-service"), so gateway/nginx.conf's
`proxy_pass http://user-service:8001/...` and nginx.conf (frontend)'s
`proxy_pass http://gateway:8080/api/` resolve correctly with zero app
changes.

ALB STATUS: Written, NOT VERIFIED. 1 public ALB in the 2 public subnets, 1
HTTP:80 listener, 1 target group (frontend, target_type "ip", health check
path "/", matching the frontend's existing nginx.conf `location /`). Only
the frontend is registered with the ALB -- /api/* traffic reaches the
gateway internally via the frontend's own existing nginx proxy_pass, not
via a second ALB rule, since that's how the app already routes it (no
redesign).

RDS STATUS: Written, NOT VERIFIED. 1 db.t3.micro PostgreSQL 16 instance,
private subnets only, publicly_accessible=false, storage encrypted,
Multi-AZ off by default (var.db_multi_az, cost tradeoff). Master password
is Terraform-generated (random_password, 32 chars) and stored in Secrets
Manager -- never in a variable, tfvars file, or task definition. NOT YET
DONE: the 4 logical databases (userdb/blogdb/categorydb/notificationdb)
that db-init/01-create-databases.sh creates automatically in the local
Postgres container do NOT get created automatically on RDS by this
Terraform -- RDS's `db_name` only creates one initial database
("postgres"), and running the create-database SQL against the real
endpoint requires network reachability from wherever `psql`/`terraform`
runs, which isn't possible with RDS correctly kept non-public. This is a
real, honestly-flagged gap -- see EXACT NEXT STEP.

SQS STATUS: Written, NOT VERIFIED. Queue name "notifications" (matches the
local ElasticMQ queue in local-sqs/elasticmq.conf exactly, so
SQS_QUEUE_URL is the only env var that changes between local dev and AWS --
SQS_ENDPOINT_URL is deliberately left unset in every ECS task definition, so
boto3 in each service falls back to the real regional SQS endpoint, exactly
as .env.example already documents). DLQ added with maxReceiveCount=5 and a
redrive_allow_policy scoping it to only accept redrives from the main
queue -- this is the "production SQS configuration" and "DLQ for
production reliability" the instructions asked for; the app's own
consume/ack logic (SQS message safety, Stage 1.5 Bug 1 fix) is unchanged.

IAM STATUS: Written, NOT VERIFIED. 2 roles: (1) a shared ECS task execution
role (ECR pull, CloudWatch Logs, and a Secrets Manager GetSecretValue policy
scoped to exactly this project's 5 secrets -- JWT + 4 DATABASE_URLs -- not
`secretsmanager:*` or `*` resources); (2) an app task role, scoped to
sqs:SendMessage/ReceiveMessage/DeleteMessage/GetQueueAttributes/
GetQueueUrl on exactly the notifications queue ARN, attached only to
user-service, blog-service, notification-service (the only 3 that touch
SQS in app code). frontend, gateway, category-service get no task role.

CLOUDWATCH STATUS: Written, NOT VERIFIED. 6 log groups
(/ecs/devopshub-<service>), 14-day retention, one per service, referenced
by both the container's own awslogs driver and its Service Connect proxy's
awslogs driver. Container Insights enabled on the cluster. No alarms were
added (not in the requested resource list; SipSugy's own "Known next
steps" flags the same gap).

---

TESTS EXECUTED: terraform fmt/validate/plan -- NOT RUN (no terraform
binary, no network, no AWS credentials in this sandbox; see TERRAFORM
STATUS). No application-level pytest/docker-compose tests were re-run in
this stage, since no application code was touched (Stage 1.5's 21/21 pass
result stands unchanged for the app itself).

TEST RESULTS: N/A -- nothing was executed in this stage that could produce
a pass/fail result. All "STATUS" lines above are marked NOT VERIFIED rather
than PASSED, deliberately.

---

KNOWN ISSUES:
- The 4 per-service RDS databases are not auto-created (see RDS STATUS) --
  needs a one-time manual step post-`terraform apply` (see EXACT NEXT STEP).
- Single NAT Gateway (not one per AZ) is a single point of failure for
  private-subnet egress if that AZ goes down; deliberate cost tradeoff,
  same pattern SipSugy's own doc flags as a known simplification.
- RDS Multi-AZ is off by default (var.db_multi_az=false) -- cost tradeoff,
  toggle-able via tfvars.
- No ACM/HTTPS listener on the ALB -- HTTP:80 only, matching the current
  scope (SipSugy's reference doc flags the identical gap: "Route 53 + ACM
  ... the ALB is currently HTTP-only").
- No CloudWatch alarms on ECS/RDS/ALB/SQS metrics -- Container Insights and
  log groups exist, but nothing pages on them yet.
- infra/modules/ec2/ and infra/modules/s3/ are now dead code (unreferenced
  from root main.tf). Left in place rather than deleted, per the minimal-
  change rule; safe to delete in a later cleanup pass if desired.

NOT VERIFIED ITEMS (everything below requires either the `terraform`
binary, AWS credentials, or both -- none available in this sandbox):
- terraform fmt / terraform validate / terraform plan
- Any actual `terraform apply` / real resource creation
- ECS Service Connect resolving service names at runtime
- ALB health checks actually passing against a running frontend task
- RDS reachability from ECS tasks, and the 4-database creation step
- SQS produce/consume against the real queue (vs. the app's existing
  ElasticMQ-based local dev path, which is untouched and still works)
- Secrets Manager secrets resolving correctly into running containers
- IAM policies being sufficient (no more, no less) in practice

EXACT NEXT STEP:
1. In an environment with the `terraform` CLI and valid AWS credentials for
   the target account/region (this repo's placeholder default is
   ap-south-1, matching the app's own AWS_REGION default): `cd infra &&
   terraform init && terraform fmt -check && terraform validate &&
   terraform plan`. Fix anything real `validate` surfaces that this
   sandbox's manual review couldn't catch, then `apply`.
2. After `apply`, run db-init/01-create-databases.sh's 4 CREATE DATABASE
   statements once against the new RDS endpoint (output as `rds_endpoint`),
   using the credentials in the `rds_master_secret_arn` Secrets Manager
   secret -- e.g. via an ECS Exec session into any running task (which is
   already in the right VPC/security group), a bastion host, or a temporary
   Session Manager tunnel. This is the one manual step Terraform
   intentionally does not automate, since RDS is correctly kept non-public.
3. Build and push the 6 Docker images (frontend, gateway, user-service,
   blog-service, category-service, notification-service) to the ECR repos
   in the `ecr_repository_urls` output, then force a new deployment on each
   ECS service so they pick up real images (the task defs default to
   `:latest`, which won't exist in a brand-new ECR repo until pushed).
4. Stage 3 (out of scope here, per instructions): rewrite the Jenkinsfile
   for ECR push + `aws ecs update-service --force-new-deployment` instead
   of the current Docker Hub + SSH-to-EC2 flow.
