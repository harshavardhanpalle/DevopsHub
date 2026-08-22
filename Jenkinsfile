```groovy
// ============================================================
// DevOpsHub - Complete CI/CD Pipeline
//
// ONE CLICK WORKFLOW:
//
// Jenkins Build Now
//      |
//      v
// Checkout Source
//      |
//      v
// Validate Required Files
//      |
//      v
// Run Python Tests
//      |
//      v
// Terraform Provision Infrastructure
//      |
//      v
// Docker Build - 6 Services
//      |
//      v
// Amazon ECR Login + Push
//      |
//      v
// Terraform Deploy ECS With New Image Tag
//      |
//      v
// Wait For ECS Stability
//      |
//      v
// ALB Health Check
// ============================================================

pipeline {

    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '15'))
    }

    environment {

        // Jenkins AWS credential ID.
        AWS_CREDENTIALS_ID = 'aws-credentials'

        // Project naming.
        PROJECT_NAME = 'devopshub'

        // AWS deployment region.
        AWS_DEFAULT_REGION = 'ap-south-1'

        // Terraform directory.
        TF_DIR = 'infrastructure/terraform'

        // Python 3.12 installed through pyenv.
        PYTHON_BIN = '/home/ubuntu/.pyenv/versions/3.12.14/bin/python'
    }

    stages {

        // ========================================================
        // 1. CHECKOUT
        // ========================================================

        stage('Checkout') {
            steps {

                checkout scm

                script {

                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG =
                        "${env.GIT_COMMIT_SHORT}-${env.BUILD_NUMBER}"

                    echo "Git commit: ${env.GIT_COMMIT_SHORT}"
                    echo "Image tag: ${env.IMAGE_TAG}"
                }
            }
        }

        // ========================================================
        // 2. VALIDATE REQUIRED FILES
        // ========================================================

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
                    infrastructure/terraform/provider.tf
                    infrastructure/terraform/variables.tf
                    infrastructure/terraform/outputs.tf
                    infrastructure/terraform/modules/ecs_cluster/main.tf
                    infrastructure/terraform/modules/ecs_cluster/variables.tf
                    "

                    missing=0

                    for f in $required_files; do

                        if [ ! -f "$f" ]; then

                            echo "MISSING REQUIRED FILE: $f"

                            missing=1

                        fi

                    done

                    if [ "$missing" -eq 1 ]; then

                        echo "One or more required files are missing."

                        exit 1

                    fi

                    echo "All required files are present."
                '''
            }
        }

        // ========================================================
        // 3. RUN TESTS
        // ========================================================

        stage('Run Tests') {
    steps {
        dir('services/user-service') {
            sh '''
                set -e

                /home/ubuntu/.pyenv/versions/3.12.14/bin/python3 -m venv .venv-ci
                . .venv-ci/bin/activate

                python --version

                pip install --upgrade pip
                pip install -r requirements.txt

                DATABASE_URL=sqlite:///./test_user_service.db \
                JWT_SECRET=ci-test-secret \
                python -m pytest -q

                deactivate
                rm -rf .venv-ci
            '''
        }
    }
}
        // ========================================================
        // 4. TERRAFORM - CREATE / UPDATE INFRASTRUCTURE
        // ========================================================

        stage('Terraform Provision Infrastructure') {
            steps {

                dir(TF_DIR) {

                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: AWS_CREDENTIALS_ID
                    ]]) {

                        sh '''
                            set -e

                            echo "========================================="
                            echo "Terraform Initialization"
                            echo "========================================="

                            terraform init -input=false

                            echo "========================================="
                            echo "Terraform Formatting Check"
                            echo "========================================="

                            terraform fmt -check -recursive

                            echo "========================================="
                            echo "Terraform Validation"
                            echo "========================================="

                            terraform validate

                            echo "========================================="
                            echo "Terraform Plan"
                            echo "========================================="

                            terraform plan \
                                -input=false \
                                -out=tfplan

                            echo "========================================="
                            echo "Terraform Apply"
                            echo "========================================="

                            terraform apply \
                                -input=false \
                                -auto-approve \
                                tfplan
                        '''
                    }
                }
            }
        }

        // ========================================================
        // 5. GET AWS ACCOUNT INFORMATION
        // ========================================================

        stage('Get AWS Account Information') {
            steps {

                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: AWS_CREDENTIALS_ID
                ]]) {

                    script {

                        env.AWS_ACCOUNT_ID = sh(
                            script: '''
                                aws sts get-caller-identity \
                                    --query Account \
                                    --output text
                            ''',
                            returnStdout: true
                        ).trim()

                        env.ECR_REGISTRY =
                            "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_DEFAULT_REGION}.amazonaws.com"

                        echo "AWS Account ID: ${env.AWS_ACCOUNT_ID}"
                        echo "ECR Registry: ${env.ECR_REGISTRY}"
                    }
                }
            }
        }

        // ========================================================
        // 6. DOCKER BUILD
        // ========================================================

        stage('Docker Build') {
            steps {

                script {

                    def images = [

                        'frontend'             : 'frontend',
                        'gateway'              : 'nginx',
                        'user-service'         : 'services/user-service',
                        'blog-service'         : 'services/blog-service',
                        'category-service'     : 'services/category-service',
                        'notification-service' : 'services/notification-service'
                    ]

                    images.each { name, buildContext ->

                        sh """
                            set -e

                            echo "========================================="
                            echo "Building ${name}"
                            echo "========================================="

                            docker build \
                                -t ${PROJECT_NAME}-${name}:${IMAGE_TAG} \
                                ${buildContext}
                        """
                    }
                }
            }
        }

        // ========================================================
        // 7. LOGIN TO AMAZON ECR
        // ========================================================

        stage('ECR Login') {
            steps {

                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: AWS_CREDENTIALS_ID
                ]]) {

                    sh '''
                        set -e

                        aws ecr get-login-password \
                            --region "$AWS_DEFAULT_REGION" \
                        | docker login \
                            --username AWS \
                            --password-stdin \
                            "$ECR_REGISTRY"
                    '''
                }
            }
        }

        // ========================================================
        // 8. PUSH ALL IMAGES TO ECR
        // ========================================================

        stage('Push Images to ECR') {
            steps {

                script {

                    def services = [
                        'frontend',
                        'gateway',
                        'user-service',
                        'blog-service',
                        'category-service',
                        'notification-service'
                    ]

                    services.each { svc ->

                        def repository =
                            "${ECR_REGISTRY}/${PROJECT_NAME}-${svc}"

                        sh """
                            set -e

                            echo "========================================="
                            echo "Pushing ${svc}"
                            echo "========================================="

                            docker tag \
                                ${PROJECT_NAME}-${svc}:${IMAGE_TAG} \
                                ${repository}:${IMAGE_TAG}

                            docker tag \
                                ${PROJECT_NAME}-${svc}:${IMAGE_TAG} \
                                ${repository}:latest

                            docker push ${repository}:${IMAGE_TAG}

                            docker push ${repository}:latest
                        """
                    }
                }
            }
        }

        // ========================================================
        // 9. TERRAFORM - DEPLOY ECS WITH NEW IMAGE TAG
        // ========================================================

        stage('Deploy New Images to ECS') {
            steps {

                dir(TF_DIR) {

                    withCredentials([[
                        $class: 'AmazonWebServicesCredentialsBinding',
                        credentialsId: AWS_CREDENTIALS_ID
                    ]]) {

                        sh '''
                            set -e

                            echo "========================================="
                            echo "Deploying Image Tag to ECS"
                            echo "Image Tag: $IMAGE_TAG"
                            echo "========================================="

                            terraform plan \
                                -input=false \
                                -var="image_tag=$IMAGE_TAG" \
                                -out=deploy-tfplan

                            terraform apply \
                                -input=false \
                                -auto-approve \
                                deploy-tfplan
                        '''
                    }
                }
            }
        }

        // ========================================================
        // 10. GET DEPLOYMENT INFORMATION
        // ========================================================

        stage('Get Deployment Information') {
            steps {

                dir(TF_DIR) {

                    script {

                        env.ECS_CLUSTER = sh(
                            script: 'terraform output -raw ecs_cluster_name',
                            returnStdout: true
                        ).trim()

                        env.ALB_DNS_NAME = sh(
                            script: 'terraform output -raw alb_dns_name',
                            returnStdout: true
                        ).trim()

                        echo "ECS Cluster: ${env.ECS_CLUSTER}"
                        echo "ALB DNS: ${env.ALB_DNS_NAME}"
                    }
                }
            }
        }

        // ========================================================
        // 11. WAIT FOR ECS STABILITY
        // ========================================================

        stage('Wait for ECS Stability') {
            steps {

                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: AWS_CREDENTIALS_ID
                ]]) {

                    sh '''
                        set -e

                        echo "========================================="
                        echo "Waiting for ECS Services"
                        echo "========================================="

                        aws ecs wait services-stable \
                            --region "$AWS_DEFAULT_REGION" \
                            --cluster "$ECS_CLUSTER" \
                            --services \
                                "${PROJECT_NAME}-frontend" \
                                "${PROJECT_NAME}-gateway" \
                                "${PROJECT_NAME}-user-service" \
                                "${PROJECT_NAME}-blog-service" \
                                "${PROJECT_NAME}-category-service" \
                                "${PROJECT_NAME}-notification-service"
                    '''
                }
            }
        }

        // ========================================================
        // 12. POST-DEPLOYMENT HEALTH CHECK
        // ========================================================

        stage('Post-Deployment Health Check') {
            steps {

                sh '''
                    set -e

                    echo "========================================="
                    echo "Checking Live Application"
                    echo "========================================="

                    echo "URL: http://$ALB_DNS_NAME/"

                    ok=0

                    for i in 1 2 3 4 5 6 7 8 9 10; do

                        echo "Health check attempt $i..."

                        if curl -sSf \
                            -o /dev/null \
                            "http://$ALB_DNS_NAME/"; then

                            ok=1
                            break

                        fi

                        echo "Application not ready yet."

                        sleep 15

                    done

                    if [ "$ok" -ne 1 ]; then

                        echo "========================================="
                        echo "DEPLOYMENT HEALTH CHECK FAILED"
                        echo "========================================="

                        exit 1

                    fi

                    echo "========================================="
                    echo "DEPLOYMENT HEALTH CHECK PASSED"
                    echo "========================================="
                '''
            }
        }
    }

    // ============================================================
    // POST BUILD ACTIONS
    // ============================================================

    post {

        success {

            script {

                echo """
============================================================

DEPLOYMENT SUCCESSFUL

Project: ${env.PROJECT_NAME}

Image Tag:
${env.IMAGE_TAG}

Live Application:
http://${env.ALB_DNS_NAME}/

============================================================
"""
            }
        }

        failure {

            echo """
============================================================

PIPELINE FAILED

Check the failed Jenkins stage above.

Terraform, Docker, ECR, ECS, or the application health
check may contain the failure details.

============================================================
"""
        }

        always {

            sh '''
                if [ -n "$ECR_REGISTRY" ]; then
                    docker logout "$ECR_REGISTRY" || true
                fi

                docker image prune -f || true
            '''
        }
    }
}
```
