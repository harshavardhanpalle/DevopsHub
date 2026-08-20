// ============================================================
// DevOpsHub -- Stage 3 CI/CD pipeline
//
// GitHub -> Jenkins -> Tests -> Docker Build -> Amazon ECR -> ECS
// Deployment -> ECS Fargate -> Application Load Balancer
//
// Replaces the Stage 1 Docker Hub + SSH-to-EC2 pipeline. That path is
// gone because Stage 2 replaced the single EC2 instance with 6 ECS
// Fargate services behind an ALB (see IMPLEMENTATION_STATUS.md /
// infrastructure/terraform/main.tf) -- there is no longer an EC2 host to SSH into, and
// Docker Hub was explicitly replaced by Amazon ECR.
//
// This file does NOT touch infrastructure/terraform/*.tf. Terraform is assumed to have
// already been applied once (creating the ECR repos, ECS cluster,
// services, and ALB that this pipeline pushes into / deploys onto).
// See EXACT NEXT STEP in IMPLEMENTATION_STATUS.md for that one-time step.
// ============================================================

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    // ------------------------------------------------------------
    // Required Jenkins credential IDs (configure in Jenkins ->
    // Manage Jenkins -> Credentials before running this pipeline):
    //
    //   aws-credentials   -- "AWS Credentials" kind (or username/password
    //                        holding AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY)
    //                        for an IAM principal allowed to: ecr:GetAuthorizationToken,
    //                        ecr:*Image*/BatchGetImage/PutImage on the 6 repos,
    //                        ecs:UpdateService/DescribeServices/RegisterTaskDefinition/
    //                        DescribeTaskDefinition, and iam:PassRole for the two
    //                        task roles in infrastructure/terraform/modules/iam.
    //
    // Required Jenkins global / job environment variables (Manage Jenkins ->
    // System, or folder-level "Environment variables"):
    //
    //   AWS_ACCOUNT_ID     -- 12-digit AWS account ID that owns the ECR repos/ECS cluster
    //   AWS_DEFAULT_REGION -- must match infrastructure/terraform/terraform.tfvars aws_region (ap-south-1)
    //
    // Nothing else needs to be configured: ECR repo names, the ECS cluster
    // name, and each service/task-family name are all derived below from
    // PROJECT_NAME using the exact naming convention Terraform itself uses
    // (infrastructure/terraform/modules/ecr/main.tf, infrastructure/terraform/modules/ecs_cluster/main.tf,
    // infrastructure/terraform/modules/ecs_service/main.tf), so this file never hardcodes an
    // account-specific ARN or URL.
    // ------------------------------------------------------------

    environment {
        AWS_CREDENTIALS_ID = 'aws-credentials'
        PROJECT_NAME        = 'devopshub'
        AWS_DEFAULT_REGION  = "${env.AWS_DEFAULT_REGION ?: 'ap-south-1'}"
        ECR_REGISTRY         = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_DEFAULT_REGION ?: 'ap-south-1'}.amazonaws.com"
        ECS_CLUSTER           = "${PROJECT_NAME}-cluster"
        TF_DIR                 = 'infrastructure/terraform'

        // Immutable tag: git commit SHA is the primary identifier so an
        // image can always be traced back to the exact commit it was built
        // from; build number is appended for human-readable uniqueness on
        // reruns of the same commit (e.g. a Jenkins retry).
        IMAGE_TAG = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(12) : 'nogit'}-${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                script {
                    // checkout scm above does not always populate env.GIT_COMMIT
                    // (depends on the configured SCM step type), so read it
                    // directly from git as a fallback for the IMAGE_TAG above.
                    if (!env.GIT_COMMIT) {
                        env.GIT_COMMIT = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    }
                    env.IMAGE_TAG = "${env.GIT_COMMIT.take(12)}-${env.BUILD_NUMBER}"
                    echo "Building commit ${env.GIT_COMMIT}, image tag: ${env.IMAGE_TAG}"
                }
            }
        }

        // Fail fast if a required project file has gone missing, instead of
        // discovering it partway through the Docker build stage.
        stage('Validate Required Files') {
            steps {
                sh '''
                    set -e
                    required_files="
                        frontend/Dockerfile
                        nginx/Dockerfile
                        services/user-service/Dockerfile
                        services/blog-service/Dockerfile
                        services/category-service/Dockerfile
                        services/notification-service/Dockerfile
                        docker-compose.yml
                        infrastructure/terraform/main.tf
                    "
                    missing=0
                    for f in $required_files; do
                        if [ ! -e "$f" ]; then
                            echo "MISSING REQUIRED FILE: $f"
                            missing=1
                        fi
                    done
                    if [ "$missing" -eq 1 ]; then
                        echo "One or more required files are missing. Aborting."
                        exit 1
                    fi
                    echo "All required files present."
                '''
            }
        }

        // Each Python microservice's tests are self-contained (SQLite
        // DATABASE_URL override, no external Postgres/SQS needed -- see
        // */tests/test_*.py). gateway and frontend are static
        // nginx/HTML with no test suite, so they are built but not tested
        // here.
        stage('Run Tests') {
            steps {
                script {
                    def services = ['user-service', 'blog-service', 'category-service', 'notification-service']
                    for (svc in services) {
                        dir("services/${svc}") {
                            sh """
                                set -e
                                python3 -m venv .venv-ci
                                . .venv-ci/bin/activate
                                pip install -q --upgrade pip
                                pip install -q -r requirements.txt
                                DATABASE_URL=sqlite:///./test_${svc.replace('-', '_')}.db \
                                JWT_SECRET=ci-test-secret \
                                python -m pytest -q
                                deactivate
                                rm -rf .venv-ci
                            """
                        }
                    }
                }
            }
        }

        // Build only the 6 images the existing architecture actually
        // deploys (matches infrastructure/terraform/main.tf's ecr_repo_names / the 6
        // ecs_service instantiations) -- no new containers, no new
        // architecture. Reuses each service's existing Dockerfile as-is.
        stage('Docker Build') {
            steps {
                script {
                    def images = [
                        'frontend'             : 'frontend',
                        'gateway'               : 'nginx',
                        'user-service'          : 'services/user-service',
                        'blog-service'          : 'services/blog-service',
                        'category-service'      : 'services/category-service',
                        'notification-service'  : 'services/notification-service',
                    ]
                    images.each { name, buildContext ->
                        sh "docker build -t ${PROJECT_NAME}-${name}:${IMAGE_TAG} ${buildContext}"
                    }
                }
            }
        }

        stage('ECR Login') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: AWS_CREDENTIALS_ID]]) {
                    sh '''
                        aws ecr get-login-password --region "$AWS_DEFAULT_REGION" \
                          | docker login --username AWS --password-stdin "$ECR_REGISTRY"
                    '''
                }
            }
        }

        stage('Push to ECR') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: AWS_CREDENTIALS_ID]]) {
                    script {
                        def services = ['frontend', 'gateway', 'user-service', 'blog-service', 'category-service', 'notification-service']
                        services.each { svc ->
                            // Repo naming matches infrastructure/terraform/modules/ecr/main.tf exactly:
                            // "${project_name}-${service}"
                            def repo = "${ECR_REGISTRY}/${PROJECT_NAME}-${svc}"
                            sh """
                                docker tag ${PROJECT_NAME}-${svc}:${IMAGE_TAG} ${repo}:${IMAGE_TAG}
                                docker tag ${PROJECT_NAME}-${svc}:${IMAGE_TAG} ${repo}:latest
                                docker push ${repo}:${IMAGE_TAG}
                                docker push ${repo}:latest
                            """
                        }
                    }
                }
            }
        }

        // Register a new task definition revision per service (image tag
        // bump only -- family, cpu/memory, roles, env, secrets are all
        // inherited from the currently running revision, which Terraform
        // created) and point each ECS service at it. No Terraform apply
        // happens here; this only updates the container image, which is
        // exactly what infrastructure/terraform/main.tf's `var.image_tag` was designed to be
        // overridden for by CI (see IMPLEMENTATION_STATUS.md EXACT NEXT
        // STEP #4).
        stage('Update ECS Task Definitions') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: AWS_CREDENTIALS_ID]]) {
                    script {
                        def services = ['frontend', 'gateway', 'user-service', 'blog-service', 'category-service', 'notification-service']
                        services.each { svc ->
                            def family = "${PROJECT_NAME}-${svc}"
                            def repo = "${ECR_REGISTRY}/${PROJECT_NAME}-${svc}"
                            sh """
                                set -e
                                CURRENT_TASK_DEF=\$(aws ecs describe-task-definition \
                                    --task-definition ${family} \
                                    --query 'taskDefinition' --output json)

                                NEW_TASK_DEF=\$(echo "\$CURRENT_TASK_DEF" | python3 -c '
import json, sys
td = json.load(sys.stdin)
for c in td["containerDefinitions"]:
    if c["name"] == "${svc}":
        c["image"] = "${repo}:${IMAGE_TAG}"
for key in ["taskDefinitionArn","revision","status","requiresAttributes",
            "compatibilities","registeredAt","registeredBy"]:
    td.pop(key, None)
print(json.dumps(td))
')
                                echo "\$NEW_TASK_DEF" > taskdef-${svc}.json
                                aws ecs register-task-definition \
                                    --cli-input-json "file://taskdef-${svc}.json" > /dev/null
                                rm -f taskdef-${svc}.json
                            """
                        }
                    }
                }
            }
        }

        stage('Deploy to ECS') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: AWS_CREDENTIALS_ID]]) {
                    script {
                        def services = ['frontend', 'gateway', 'user-service', 'blog-service', 'category-service', 'notification-service']
                        services.each { svc ->
                            def family = "${PROJECT_NAME}-${svc}"
                            sh """
                                aws ecs update-service \
                                    --cluster ${ECS_CLUSTER} \
                                    --service ${family} \
                                    --task-definition ${family} \
                                    --force-new-deployment > /dev/null
                            """
                        }
                    }
                }
            }
        }

        stage('Wait for ECS Stability') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: AWS_CREDENTIALS_ID]]) {
                    script {
                        def services = ['frontend', 'gateway', 'user-service', 'blog-service', 'category-service', 'notification-service']
                        def serviceNames = services.collect { "${PROJECT_NAME}-${it}" }.join(' ')
                        // `aws ecs wait services-stable` times out at 10 min by
                        // default; if it fails, surface it but let the health
                        // check stage make the final pass/fail call rather than
                        // failing the whole pipeline on a slow-but-fine rollout.
                        sh """
                            aws ecs wait services-stable --cluster ${ECS_CLUSTER} --services ${serviceNames} \
                              || echo "WARNING: services-stable wait did not confirm steady state in time -- continuing to health check"
                        """
                    }
                }
            }
        }

        // Read the ALB DNS name from Terraform state (already-applied
        // Stage 2 infra) rather than hardcoding it, and hit the live site
        // through the ALB -- the same path a real user takes.
        stage('Post-Deployment Health Check') {
            steps {
                dir(TF_DIR) {
                    script {
                        env.ALB_DNS_NAME = sh(
                            script: 'terraform output -raw alb_dns_name',
                            returnStdout: true
                        ).trim()
                    }
                }
                sh '''
                    set -e
                    echo "Checking ALB: http://$ALB_DNS_NAME/"
                    ok=0
                    for i in 1 2 3 4 5 6; do
                        if curl -sSf -o /dev/null "http://$ALB_DNS_NAME/"; then
                            ok=1
                            break
                        fi
                        echo "Attempt $i: not healthy yet, retrying in 15s..."
                        sleep 15
                    done
                    if [ "$ok" -ne 1 ]; then
                        echo "Health check FAILED against http://$ALB_DNS_NAME/"
                        exit 1
                    fi
                    echo "Health check PASSED against http://$ALB_DNS_NAME/"
                '''
            }
        }
    }

    post {
        success {
            echo "Deployment successful. Live site: http://${env.ALB_DNS_NAME}/  (image tag: ${env.IMAGE_TAG})"
        }
        failure {
            echo "Pipeline failed. Check stage logs above."
        }
        always {
            sh 'docker logout "$ECR_REGISTRY" || true'
        }
    }
}
