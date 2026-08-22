```groovy
// ============================================================
// DevOpsHub - Complete CI/CD Pipeline
//
// WORKFLOW:
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
// Run Python Tests using Python 3.12.14
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

        // ========================================================
        // Jenkins Credentials
        // ========================================================

        AWS_CREDENTIALS_ID = 'aws-credentials'


        // ========================================================
        // Project Configuration
        // ========================================================

        PROJECT_NAME = 'devopshub'

        AWS_DEFAULT_REGION = 'ap-south-1'

        TF_DIR = 'infrastructure/terraform'


        // ========================================================
        // Python Configuration
        //
        // Python 3.12.14 installed using pyenv.
        //
        // This absolute path is required because Jenkins runs as
        // the "jenkins" user and Ubuntu's default Python is 3.14.
        // ========================================================

        PYTHON_BIN = '/home/ubuntu/.pyenv/versions/3.12.14/bin/python'
    }

    stages {

        // ========================================================
        // 1. CHECKOUT SOURCE CODE
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

                    echo "========================================="
                    echo "Checkout Complete"
                    echo "========================================="

                    echo "Git Commit: ${env.GIT_COMMIT_SHORT}"
                    echo "Build Number: ${env.BUILD_NUMBER}"
                    echo "Image Tag: ${env.IMAGE_TAG}"
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

                    echo "========================================="
                    echo "Validating Required Files"
                    echo "========================================="

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

                        echo "========================================="
                        echo "VALIDATION FAILED"
                        echo "========================================="

                        exit 1

                    fi

                    echo "========================================="
                    echo "All Required Files Are Present"
                    echo "========================================="
                '''
            }
        }


        // ========================================================
        // 3. VERIFY PYTHON
        // ========================================================

        stage('Verify Python Environment') {

            steps {

                sh '''
                    set -e

                    echo "========================================="
                    echo "Verifying Python Environment"
                    echo "========================================="

                    echo "Python Binary:"
                    echo "$PYTHON_BIN"

                    if [ ! -x "$PYTHON_BIN" ]; then

                        echo "ERROR: Python binary does not exist or is not executable."

                        exit 1
                    fi

                    "$PYTHON_BIN" --version

                    "$PYTHON_BIN" -m pip --version || true

                    echo "========================================="
                    echo "Python Environment Verified"
                    echo "========================================="
                '''
            }
        }


        // ========================================================
        // 4. RUN PYTHON TESTS
        //
        // Each service gets its own temporary virtual environment.
        //
        // Jenkins explicitly uses Python 3.12.14.
        // ========================================================

        stage('Run Tests') {

            steps {

                script {

                    def services = [
                        'user-service',
                        'blog-service',
                        'category-service',
                        'notification-service'
                    ]

                    for (svc in services) {

                        dir("services/${svc}") {

                            sh """
                                set -e

                                echo "========================================="
                                echo "Testing ${svc}"
                                echo "========================================="

                                echo "Creating Python virtual environment..."

                                "\$PYTHON_BIN" -m venv .venv-ci

                                . .venv-ci/bin/activate

                                echo "Python Version:"
                                python --version

                                echo "Upgrading pip..."

                                python -m pip install \
                                    --upgrade pip

                                echo "Installing dependencies..."

                                python -m pip install \
                                    -r requirements.txt

                                echo "Running tests..."

                                DATABASE_URL=sqlite:///./test_${svc.replace('-', '_')}.db \\
                                JWT_SECRET=ci-test-secret \\
                                python -m pytest -q

                                echo "Cleaning up..."

                                deactivate || true

                                rm -rf .venv-ci

                                rm -f test_${svc.replace('-', '_')}.db

                                echo "========================================="
                                echo "${svc} Tests Passed"
                                echo "========================================="
                            """
                        }
                    }
                }
            }
        }


        // ========================================================
        // 5. TERRAFORM - PROVISION INFRASTRUCTURE
        //
        // Creates / updates infrastructure including:
        //
        // VPC
        // Subnets
        // NAT Gateway
        // Security Groups
        // ECR
        // SQS
        // Secrets Manager
        // RDS
        // IAM
        // ECS Cluster
        // Service Connect
        // Application Load Balancer
        // ECS Services
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

                            terraform fmt \
                                -check \
                                -recursive


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
        // 6. GET AWS ACCOUNT INFORMATION
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
                                set -e

                                aws sts get-caller-identity \
                                    --query Account \
                                    --output text
                            ''',
                            returnStdout: true
                        ).trim()


                        env.ECR_REGISTRY =
                            "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_DEFAULT_REGION}.amazonaws.com"


                        echo "========================================="
                        echo "AWS Account Information"
                        echo "========================================="

                        echo "AWS Account ID: ${env.AWS_ACCOUNT_ID}"

                        echo "AWS Region: ${env.AWS_DEFAULT_REGION}"

                        echo "ECR Registry: ${env.ECR_REGISTRY}"
                    }
                }
            }
        }


        // ========================================================
        // 7. DOCKER BUILD - 6 SERVICES
        // ========================================================

        stage('Docker Build') {

            steps {

                script {

                    def images = [

                        'frontend' :
                            'frontend',

                        'gateway' :
                            'nginx',

                        'user-service' :
                            'services/user-service',

                        'blog-service' :
                            'services/blog-service',

                        'category-service' :
                            'services/category-service',

                        'notification-service' :
                            'services/notification-service'
                    ]


                    images.each { name, buildContext ->

                        sh """
                            set -e

                            echo "========================================="
                            echo "Building Docker Image"
                            echo "Service: ${name}"
                            echo "Context: ${buildContext}"
                            echo "========================================="

                            docker build \
                                -t ${PROJECT_NAME}-${name}:${IMAGE_TAG} \
                                ${buildContext}

                            echo "Successfully built:"
                            echo "${PROJECT_NAME}-${name}:${IMAGE_TAG}"
                        """
                    }
                }
            }
        }


        // ========================================================
        // 8. LOGIN TO AMAZON ECR
        // ========================================================

        stage('ECR Login') {

            steps {

                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: AWS_CREDENTIALS_ID
                ]]) {

                    sh '''
                        set -e

                        echo "========================================="
                        echo "Logging Into Amazon ECR"
                        echo "========================================="

                        aws ecr get-login-password \
                            --region "$AWS_DEFAULT_REGION" \
                        | docker login \
                            --username AWS \
                            --password-stdin \
                            "$ECR_REGISTRY"

                        echo "Successfully logged into ECR."
                    '''
                }
            }
        }


        // ========================================================
        // 9. PUSH DOCKER IMAGES TO ECR
        //
        // Each image receives:
        //
        // 1. Immutable Jenkins build tag
        // 2. latest tag
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
                            echo "Repository:"
                            echo "${repository}"
                            echo "========================================="

                            docker tag \
                                ${PROJECT_NAME}-${svc}:${IMAGE_TAG} \
                                ${repository}:${IMAGE_TAG}


                            docker tag \
                                ${PROJECT_NAME}-${svc}:${IMAGE_TAG} \
                                ${repository}:latest


                            docker push \
                                ${repository}:${IMAGE_TAG}


                            docker push \
                                ${repository}:latest


                            echo "${svc} pushed successfully."
                        """
                    }
                }
            }
        }


        // ========================================================
        // 10. DEPLOY NEW IMAGE TAG TO ECS
        //
        // Terraform updates ECS task definitions with the new
        // immutable image tag generated by Jenkins.
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
                            echo "Deploying New Images to ECS"
                            echo "========================================="

                            echo "Image Tag: $IMAGE_TAG"


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
        // 11. GET DEPLOYMENT INFORMATION
        // ========================================================

        stage('Get Deployment Information') {

            steps {

                dir(TF_DIR) {

                    script {

                        env.ECS_CLUSTER = sh(
                            script: '''
                                terraform output \
                                    -raw \
                                    ecs_cluster_name
                            ''',
                            returnStdout: true
                        ).trim()


                        env.ALB_DNS_NAME = sh(
                            script: '''
                                terraform output \
                                    -raw \
                                    alb_dns_name
                            ''',
                            returnStdout: true
                        ).trim()


                        echo "========================================="
                        echo "Deployment Information"
                        echo "========================================="

                        echo "ECS Cluster:"
                        echo "${env.ECS_CLUSTER}"

                        echo "ALB DNS Name:"
                        echo "${env.ALB_DNS_NAME}"

                        echo "Application URL:"
                        echo "http://${env.ALB_DNS_NAME}/"
                    }
                }
            }
        }


        // ========================================================
        // 12. WAIT FOR ECS SERVICES TO BECOME STABLE
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
                        echo "Waiting For ECS Services"
                        echo "========================================="

                        echo "Cluster: $ECS_CLUSTER"


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


                        echo "========================================="
                        echo "All ECS Services Are Stable"
                        echo "========================================="
                    '''
                }
            }
        }


        // ========================================================
        // 13. POST-DEPLOYMENT HEALTH CHECK
        //
        // Jenkins attempts the ALB endpoint up to 10 times.
        // ========================================================

        stage('Post-Deployment Health Check') {

            steps {

                sh '''
                    set -e

                    echo "========================================="
                    echo "Checking Live Application"
                    echo "========================================="

                    echo "URL:"
                    echo "http://$ALB_DNS_NAME/"


                    ok=0


                    for i in 1 2 3 4 5 6 7 8 9 10; do

                        echo "========================================="

                        echo "Health Check Attempt $i of 10"

                        echo "========================================="


                        if curl \
                            -sSf \
                            -o /dev/null \
                            "http://$ALB_DNS_NAME/"; then

                            ok=1

                            break

                        fi


                        echo "Application is not ready yet."

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

Project:
${env.PROJECT_NAME}

Git Commit:
${env.GIT_COMMIT_SHORT}

Image Tag:
${env.IMAGE_TAG}

ECS Cluster:
${env.ECS_CLUSTER}

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

Check the Jenkins console output.

The failure may be in one of these areas:

- Python tests
- Terraform
- AWS credentials
- Docker build
- Amazon ECR
- ECS deployment
- ECS service stability
- Application Load Balancer health check

Fix the exact failed stage shown in Jenkins.

============================================================
"""
        }


        always {

            sh '''
                echo "========================================="
                echo "Pipeline Cleanup"
                echo "========================================="

                if [ -n "$ECR_REGISTRY" ]; then

                    docker logout \
                        "$ECR_REGISTRY" || true

                fi


                docker image prune \
                    -f || true


                echo "Cleanup Complete."
            '''
        }
    }
}
```
