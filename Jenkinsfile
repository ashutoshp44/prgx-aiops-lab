pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REPO = 'prgx-aiops-api'
        IMAGE_TAG = '3.0'
        ECR_REGISTRY = '811320358992.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_IMAGE = "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .venv-ci
                    . .venv-ci/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m compileall app
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build -t ${ECR_REPO}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Trivy Scan') {
            steps {
                sh '''
                    trivy image --severity HIGH,CRITICAL ${ECR_REPO}:${IMAGE_TAG}
                '''
            }
        }

        stage('ECR Login') {
            steps {
                sh '''
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
                '''
            }
        }

        stage('ECR Push') {
            steps {
                sh '''
                    docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_IMAGE}
                    docker push ${ECR_IMAGE}
                '''
            }
        }

        stage('Verify ECR Image') {
            steps {
                sh '''
                    aws ecr describe-images \
                      --repository-name ${ECR_REPO} \
                      --image-ids imageTag=${IMAGE_TAG} \
                      --region ${AWS_REGION}
                '''
            }
        }
    }

    post {
        always {
            sh 'rm -rf .venv-ci || true'
        }

        success {
            echo 'PRGX AIOps CI/CD pipeline completed successfully.'
        }

        failure {
            echo 'PRGX AIOps CI/CD pipeline failed.'
        }
    }
}
