pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REPO = 'prgx-aiops-api'
        IMAGE_TAG = "${BUILD_NUMBER}"
        ECR_REGISTRY = '811320358992.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_IMAGE = "${ECR_REGISTRY}/${ECR_REPO}:${IMAGE_TAG}"
        LOCAL_IMAGE = "${ECR_REPO}:${IMAGE_TAG}"
        CONTAINER_NAME = 'prgx-aiops-api'
        APP_PORT = '8002'
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
                    set -e

                    python3 -m venv .venv-ci
                    . .venv-ci/bin/activate

                    pip install --upgrade pip
                    pip install -r requirements.txt

                    python -m compileall app

                    echo "Starting temporary test container..."

                    docker build --pull -t ${LOCAL_IMAGE} .

                    docker rm -f prgx-aiops-test 2>/dev/null || true

                    docker run -d \
                        --name prgx-aiops-test \
                        -p 8001:8000 \
                        ${LOCAL_IMAGE}

                    sleep 5

                    echo "Testing /health..."
                    curl --fail --silent --show-error \
                        http://127.0.0.1:8001/health

                    echo
                    echo "Testing /predict..."
                    curl --fail --silent --show-error \
                        http://127.0.0.1:8001/predict

                    echo
                    echo "Stopping test container..."
                    docker rm -f prgx-aiops-test
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

                    echo "Docker image built successfully."
                    docker images ${LOCAL_IMAGE}
                '''
            }
        }

        stage('Docker Security Check') {
            steps {
                sh '''
                    set -e

                    USER_INFO=$(docker run --rm ${LOCAL_IMAGE} id)

                    echo "Container user:"
                    echo "${USER_INFO}"

                    echo "${USER_INFO}" | grep -q "uid=1000"

                    echo "Non-root container security check passed."
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
                        --ignore-unfixed \
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

                    echo "ECR login successful."
                '''
            }
        }

        stage('Push to ECR') {
            steps {
                sh '''
                    set -e

                    docker tag ${LOCAL_IMAGE} ${ECR_IMAGE}

                    docker push ${ECR_IMAGE}

                    echo "Image pushed successfully:"
                    echo "${ECR_IMAGE}"
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

                    echo "ECR image verification successful."
                '''
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                    set -e

                    echo "Deploying verified image:"
                    echo "${ECR_IMAGE}"

                    PREVIOUS_IMAGE=""

                    OLD_CONTAINER=$(docker ps \
                        --filter "publish=${APP_PORT}" \
                        --format "{{.ID}}" | head -n 1 || true)

                    if [ -n "${OLD_CONTAINER}" ]; then
                        PREVIOUS_IMAGE=$(docker inspect "${OLD_CONTAINER}" \
                            --format '{{.Config.Image}}' || true)
                        echo "Previous image: ${PREVIOUS_IMAGE}"
                    fi

                    echo "Pulling new image..."
                    docker pull ${ECR_IMAGE}

                    echo "Freeing port ${APP_PORT}..."

                    docker ps \
                        --filter "publish=${APP_PORT}" \
                        --format "{{.ID}}" | \
                    xargs -r docker rm -f

                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                    echo "Starting new container..."

                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        -p ${APP_PORT}:8000 \
                        --restart unless-stopped \
                        ${ECR_IMAGE}

                    echo "Waiting for startup..."
                    sleep 5

                    DEPLOY_OK=true

                    echo "Health check..."
                    if ! curl --fail --silent --show-error \
                        http://127.0.0.1:${APP_PORT}/health; then
                        DEPLOY_OK=false
                    fi

                    echo
                    echo "Prediction check..."
                    if [ "${DEPLOY_OK}" = "true" ]; then
                        if ! curl --fail --silent --show-error \
                            http://127.0.0.1:${APP_PORT}/predict; then
                            DEPLOY_OK=false
                        fi
                    fi

                    echo

                    if [ "${DEPLOY_OK}" = "true" ]; then
                        echo "Deployment successful."
                        docker inspect ${CONTAINER_NAME} \
                            --format '{{.Config.Image}}'
                    else
                        echo "Deployment failed."

                        docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                        if [ -n "${PREVIOUS_IMAGE}" ]; then
                            echo "Rolling back to ${PREVIOUS_IMAGE}..."

                            docker pull "${PREVIOUS_IMAGE}"

                            docker run -d \
                                --name ${CONTAINER_NAME} \
                                -p ${APP_PORT}:8000 \
                                --restart unless-stopped \
                                "${PREVIOUS_IMAGE}"

                            sleep 5

                            curl --fail --silent --show-error \
                                http://127.0.0.1:${APP_PORT}/health

                            echo

                            curl --fail --silent --show-error \
                                http://127.0.0.1:${APP_PORT}/predict

                            echo
                            echo "Rollback successful."
                        else
                            echo "No previous image available."
                        fi

                        exit 1
                    fi
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f prgx-aiops-test 2>/dev/null || true
                rm -rf .venv-ci || true
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
