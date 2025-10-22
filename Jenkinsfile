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
        SONAR_HOST_URL='http://192.168.50.4:9000'
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
              sh '''
              echo "⚙️ Running Python Unit Test..."
              docker run --rm \
              -v $(pwd):/app \
              -w /app \
              python:3.8 \
              bash -c "pip install --quiet -r requirements.txt && PYTHONPATH=/app pytest tests/ --maxfail=1 --disable-warnings -q --junitxml=pytest-report.xml"
              '''
          }
           post {
             success {echo '✅ Unit tests passed successfully.'}
             failure {echo '❌ Unit tests failed.'}
           }
        }

        stage('Static Analysis - SonarQube & Bandit') {
            parallel {

                stage('SonarQube Analysis') {
                    steps {
                           echo "🔎 Running SonarQube scan for Python project..."
                           sh '''
                             docker run --rm \
                            -v $(pwd):/usr/src \
                            -e SONAR_HOST_URL=$SONAR_HOST_URL \
                            -e SONAR_TOKEN=$SONAR_AUTH_TOKEN \
                            sonarsource/sonar-scanner-cli:latest \
                            -Dsonar.projectKey=devsecops \
                            -Dsonar.projectName=$IMAGE_NAME \
                            -Dsonar.projectVersion=1.0 \
                            -Dsonar.sources=/usr/src \
                            -Dsonar.language=py \
                            -Dsonar.sourceEncoding=UTF-8
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
        stage('Secrets Scan - GitLeaks') {
            steps {
                sh '''
                    echo "Running GitLeaks..."
                    docker run --rm -v $(pwd):/repo zricethezav/gitleaks:latest \
                    detect --source /repo --report-format json \
                    --report-path /repo/gitleaks-report.json || true
                '''
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

        stage("Trivy Scan") {
         steps {
            script {
                def imageTag = "${IMAGE_NAME}:${BUILD_NUMBER}"
                    echo "🔍 Running Trivy scan on ${imageTag}"

                    echo "⏳ Updating Trivy DB..."
                    sh 'trivy image --download-db-only'

                    echo "🔎 Scanning built image..."
                    sh '''
                    trivy image --exit-code 1 --severity HIGH,CRITICAL --format json -o trivy-report.json ${imageTag}
                    '''

                    echo "🖥️ Scanning filesystem (optional)..."
                    sh '''
                     trivy fs --exit-code 1 --severity HIGH,CRITICAL --format json -o trivy-fs-report.json .
                    ''' 
                    }
               }
        }
    
        stage('Dynamic Analysis - OWASP ZAP & Wapiti') {
          parallel{
             stage('OWASP ZAP'){
               steps {
                script {
                    echo "Starting vulnerable container for DAST..."
                    sh "docker run -d -p 5005:5005 --name test-${BUILD_NUMBER} ${IMAGE_NAME}:${BUILD_NUMBER}"
                    sleep(10)

                    echo "Running OWASP ZAP scan..."
                    sh '''
                        docker run --rm -v $(pwd):/zap/wrk/:rw \
                        owasp/zap2docker-stable zap-baseline.py \
                        -t http://host.docker.internal:5005 \
                        -r zap_report.html || true
                    '''
                }
               }
             }
             stage('Wapiti'){
                steps{
                  script{
                
                    echo "Running Wapiti scan..."
                    sh '''
                        docker run --rm -v $(pwd):/tmp/ \
                        projectdiscovery/wapiti \
                        -u http://host.docker.internal:5000 \
                        -f html -o wapiti_report.html || true
                    '''

                    sh "docker stop test-${BUILD_NUMBER}"
                  }
                }
              }
          }
        }

    }    
     
    post {
        always {
            echo "📦 Archiving scan reports..."
            archiveArtifacts artifacts: '**/*.xml,**/*.json,**/*.txt,**/*.html', allowEmptyArchive: true
        }
    }

}

