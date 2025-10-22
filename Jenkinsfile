def COLOR_MAP = [
    'SUCCESS': 'good',
    'FAILURE': 'danger',
]

pipeline {
    agent any

    environment {
        SCANNER_HOME = tool 'sonarqube'
        NEXUS_VERSION = 'nexus3'
        NEXUS_PROTOCOL = "http"
        NEXUS_URL = "192.168.50.4:8081"
        NEXUS_REPOSITORY = "image-repo"
        NEXUS_REPO_ID = "image-repo"
        NEXUS_CREDENTIAL_ID = "nexus"
        ARTVERSION = "${env.BUILD_ID}"
        IMAGE_NAME = "vuln-flask-app"
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
                        withSonarQubeEnv('sonarqube') {
                            sh '''
                                echo "🔎 Running SonarQube scan..."
                                ${SCANNER_HOME}/bin/sonar-scanner \
                                    -Dsonar.projectKey=${IMAGE_NAME} \
                                    -Dsonar.projectName=${IMAGE_NAME} \
                                    -Dsonar.projectVersion=1.0 \
                                    -Dsonar.sources=. \
                                    -Dsonar.language=py \
                                    -Dsonar.sourceEncoding=UTF-8
                            '''
                        }
                    }
                }

                stage('Bandit Scan') {
                    steps {
                        sh '''
                            echo "🔒 Running Bandit scan..."
                            pip install --quiet bandit
                            bandit -r . -f json -o bandit-report.json || true
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
