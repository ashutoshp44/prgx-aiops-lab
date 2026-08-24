pipeline {
    agent any

    environment {
        AWS_REGION   = 'ap-south-1'
        ECR_REPO     = 'prgx-aiops-api'
        ECR_REGISTRY = '811320358992.dkr.ecr.ap-south-1.amazonaws.com'

        IMAGE_TAG   = "${BUILD_NUMBER}"
        LOCAL_IMAGE = "${ECR_REPO}:${BUILD_NUMBER}"
        ECR_IMAGE  = "${ECR_REGISTRY}/${ECR_REPO}:${BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                sh '''
                    set -e
                    echo "Workspace:"
                    pwd
                    echo "Files:"
                    find . -maxdepth 2 -type f | sort
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set -e

                    python3 -m venv .venv-ci
                    . .venv-ci/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt

                    python -m compileall app

                    uvicorn app.main:app \
                        --host 127.0.0.1 \
                        --port 9000 \
                        > /tmp/prgx-api-test.log 2>&1 &

                    APP_PID=$!
                    trap 'kill $APP_PID 2>/dev/null || true' EXIT

                    sleep 3

                    curl --fail http://127.0.0.1:9000/health
                    echo

                    curl --fail http://127.0.0.1:9000/predict
                    echo
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    set -e

                    docker build \
                        -t ${LOCAL_IMAGE} \
                        .

                    docker images ${ECR_REPO}
                '''
            }
        }

        stage('Docker Security Check') {
            steps {
                sh '''
                    set -e

                    USER_ID=$(docker inspect \
                        ${LOCAL_IMAGE} \
                        --format '{{.Config.User}}')

                    echo "Container user: ${USER_ID}"

                    if [ "${USER_ID}" != "appuser" ]; then
                        echo "ERROR: Container is not running as appuser."
                        exit 1
                    fi

                    docker run --rm ${LOCAL_IMAGE} id
                '''
            }
        }

        stage('Trivy Scan') {
            steps {
                sh '''
                    set -e

                    echo "Running Trivy vulnerability scan..."

                    trivy image \
                        --config /dev/null \
                        --ignorefile /dev/null \
                        --severity HIGH,CRITICAL \
                        --exit-code 1 \
                        --scanners vuln \
                        ${LOCAL_IMAGE}

                    echo "Trivy security scan passed."
                '''
            }
        }

        stage('ECR Login') {
            steps {
                sh '''
                    set -e

                    aws ecr get-login-password \
                        --region ${AWS_REGION} | \
                    docker login \
                        --username AWS \
                        --password-stdin ${ECR_REGISTRY}
                '''
            }
        }

        stage('Push to ECR') {
            steps {
                sh '''
                    set -e

                    docker tag \
                        ${LOCAL_IMAGE} \
                        ${ECR_IMAGE}

                    docker push ${ECR_IMAGE}
                '''
            }
        }

        stage('Verify ECR Image') {
            steps {
                sh '''
                    set -e

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
            sh '''
                rm -rf .venv-ci || true
                rm -f /tmp/prgx-api-test.log || true
                docker image rm ${LOCAL_IMAGE} 2>/dev/null || true
                docker image rm ${ECR_IMAGE} 2>/dev/null || true
            '''
        }

        success {
            echo 'PRGX AIOps CI/CD pipeline completed successfully.'
        }

        failure {
            echo 'PRGX AIOps CI/CD pipeline failed.'
        }
    }
}
