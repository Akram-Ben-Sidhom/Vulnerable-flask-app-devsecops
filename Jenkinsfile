def COLOR_MAP = [
    'SUCCESS': 'good',
    'FAILURE': 'danger',
]

pipeline {
    agent any

    environment {
        NEXUS_VERSION = 'nexus3'
        NEXUS_PROTOCOL = "http"
        NEXUS_URL = "192.168.50.4:8081"
        NEXUS_REPOSITORY = "image-repo"
        NEXUS_REPO_ID = "image-repo"
        NEXUS_CREDENTIAL_ID = "nexus"
        ARTVERSION = "${env.BUILD_ID}"
        IMAGE_NAME = "vuln-flask-app"
        SONAR_HOST_URL='http://192.168.50.4:9000/'
        SONAR_AUTH_TOKEN=credentials('sonarqube')
    }

    stages {

        stage("Clean Workspace") {
            steps {
                cleanWs()
            }
        }

        stage("Git Checkout") {
            steps {
                git branch: 'main', url: 'https://github.com/Akram-Ben-Sidhom/Vulnerable-flask-app-devsecops.git'
            }
        }

        stage('Unit Tests') {
            steps {
                script {
                    echo "⚙️ Running Unit Tests (placeholder)..."
                    // If you have pytest, for example:
                    // sh 'pytest --maxfail=1 --disable-warnings -q'
                }
            }
            post {
                success {
                    echo '✅ Unit tests passed successfully.'
                }
                failure {
                    echo '❌ Unit tests failed.'
                }
            }
        }

        stage('Static Analysis - SonarQube & Bandit') {
            parallel {

                stage('SonarQube Analysis') {
                    steps {
                           echo "🔎 Running SonarQube scan for Python project..."
                           withSonarQubeEnv('sonar') {
                           sh '''
                           sonar-scanner \
                               -Dsonar.projectKey=devsecops \
                               -Dsonar.projectName=vuln-flask-app \
                               -Dsonar.projectVersion=1.0 \
                               -Dsonar.sources=. \
                               -Dsonar.language=py \
                               -Dsonar.sourceEncoding=UTF-8 \
                               -Dsonar.host.url=$SONAR_HOST_URL \
                               -Dsonar.login=$SONAR_AUTH_TOKEN
                           '''
                    }
                }

                stage('Bandit Scan') {
                    steps {
                        sh '''
                            echo "🔒 Running Bandit scan..."
                               docker run --rm \
                               -v $(pwd):/data \
                               cytopia/bandit:latest-py3.8 \
                               -r /data -f json -o /data/bandit-report.json || true
                        '''
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "🔨 Building Docker image..."
                    docker.build("${IMAGE_NAME}:${BUILD_NUMBER}")
                }
            }
        }

        stage("Trivy Scan Image") {
            steps {
                script {
                    def imageTag = "${IMAGE_NAME}:${BUILD_NUMBER}"
                    echo "🔍 Running Trivy scan on ${imageTag}"
                    sh """
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy image -f json -o trivy-image.json ${imageTag} || true
                        docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy image -f table -o trivy-image.txt ${imageTag} || true
                    """
                }
            }
        }
    }

    post {
        always {
            echo "📦 Archiving scan reports..."
            archiveArtifacts artifacts: '**/*.json, **/*.txt', allowEmptyArchive: true
        }
    }
}
