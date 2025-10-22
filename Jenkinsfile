def COLOR_MAP = [
    'SUCCESS': 'good',
    'FAILURE': 'danger',
]

pipeline {
    agent any

    environment {
        NEXUS_URL = "http://192.168.50.4:8081"
        NEXUS_REPOSITORY = "image-repo"
        NEXUS_CREDENTIAL_ID = "nexus"
        ARTVERSION = "${env.BUILD_ID}"
        IMAGE_NAME = "vuln-flask-app"
        SONAR_HOST_URL='http://192.168.50.4:9000'
        SONAR_AUTH_TOKEN=credentials('sonarqube')
        SLACK_CHANNEL = '#pipeline-notif'
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
        stage('Images Cleanup') {
         steps {
           script {
           def prevBuild = (BUILD_NUMBER.toInteger() - 1)
            if (prevBuild > 0) {
                def prevContainer = "test-${prevBuild}"
                def prevImage = "${IMAGE_NAME}:${prevBuild}"

                // Remove previous container if exists
                sh "docker remove ${prevContainer} || true"

                // Remove previous image if exists
                sh "docker image remove ${prevImage} || true"

                echo "✅ Removed previous container (${prevContainer}) and image (${prevImage})"
              } else {
                echo "ℹ️ No previous build to clean up"
             }
           }
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

                    echo "🖥️ Scanning filesystem ..."
                    sh '''
                     trivy fs --exit-code 1 --severity HIGH,CRITICAL --format json -o trivy-fs-report.json . || true
                    ''' 
                    // here used the or true to continue and evade the exit code because of vulnerabilities found (just for test only)
                    echo "🔎 Scanning built image..."
                    sh """
                    trivy image --exit-code 1 --severity HIGH,CRITICAL --format json -o trivy-report.json ${imageTag} || true 
                    """

                    }
               }
        }
    
          
        stage('DAST OWASP ZAP'){
               steps {
                script {
                    echo "Starting vulnerable container for DAST..."
                    sh "docker run -d -p 5005:5005 --name test-${BUILD_NUMBER} ${IMAGE_NAME}:${BUILD_NUMBER}"
                    sleep(20)

                    echo '🔍 Running OWASP ZAP baseline scan...'

                    // Run ZAP but ignore exit code
                    def exitCode = sh(script: '''
                        docker run --rm --user root --network host -v $(pwd):/zap/wrk:rw \
                        -t zaproxy/zap-stable zap-full-scan.py \
                        -t http://localhost:5005/login \
                        -r zap_full_report.html -J zap_full_report.json
                    ''', returnStatus: true)

                    echo "ZAP scan finished with exit code: ${exitCode}"

                    // Read the JSON report if it exists
                    if (fileExists('zap_full_report.json')) {
                        def zapJson = readJSON file: 'zap_full_report.json'

                        def highCount = zapJson.site.collect { site ->
                            site.alerts.findAll { it.risk == 'High' }.size()
                        }.sum()

                        def mediumCount = zapJson.site.collect { site ->
                            site.alerts.findAll { it.risk == 'Medium' }.size()
                        }.sum()

                        def lowCount = zapJson.site.collect { site ->
                            site.alerts.findAll { it.risk == 'Low' }.size()
                        }.sum()

                        echo "✅ High severity issues: ${highCount}"
                        echo "⚠️ Medium severity issues: ${mediumCount}"
                        echo "ℹ️ Low severity issues: ${lowCount}"
                    } else {
                        echo "ZAP JSON report not found, continuing build..."
                    }
                }
               }
        }    


        stage('DAST Wapiti'){
                steps{
                  script{
                    if (!fileExists('./reports')) {
                        sh 'mkdir -p ./reports'
                    }
                    echo "Running Wapiti scan..."

                    sh '''
                        docker run --name wapiti-test \
                        --user root \
                        wildwildangel/wapiti \
                        -u http://localhost:5005/login \
                        -f html -o /root/wapiti_report.html || true
                    '''
                    echo "getting the wapiti report now"
                    sh 'docker cp wapiti-test:/root/wapiti_report.html ./reports/wapiti_report.html'
                    echo "Wapiti Scan Finished"
                    echo "Closing Instance Now"
                    sh 'docker rm -f wapiti-test'
                    sh "docker stop test-${BUILD_NUMBER}"

                  }
                }
        } 

        stage('Publish Secure Docker Image Into Nexus') {
         steps {
           script {
            def imageTag = "${IMAGE_NAME}:${BUILD_NUMBER}"
            def nexusImageTag = "NEXUS/${NEXUS_REPOSITORY}/${imageTag}"

            withCredentials([usernamePassword(credentialsId: "${NEXUS_CREDENTIAL_ID}", 
                                             usernameVariable: 'NEXUS_USER', 
                                             passwordVariable: 'NEXUS_PASSWORD')]) {
                sh "echo $NEXUS_PASSWORD | docker login ${NEXUS_URL} -u $NEXUS_USER --password-stdin"

                echo " Tagging image for Nexus..."
                sh "docker tag ${imageTag} ${nexusImageTag}"

                echo " Pushing image to Nexus..."
                sh "docker push ${nexusImageTag}"

                echo "✅ Image pushed: ${nexusImageTag}"
            }
            }
         }
        }
        

    }    
     
    post {
        always {
            script{
            echo "📦 Archiving scan reports..."
            archiveArtifacts artifacts: '**/*.xml,**/*.json,**/*.txt,**/*.html', allowEmptyArchive: true
            
                def buildStatus = currentBuild.currentResult
                def buildUser = currentBuild.getBuildCauses('hudson.model.Cause$UserIdCause')[0]?.userId ?: 'GitHub User'
                def buildUrl = "${env.BUILD_URL}"
                echo "📦 Slack notif "

                slackSend(
                    channel: "${SLACK_CHANNEL}",
                    color: COLOR_MAP[buildStatus],
                    message: """*${buildStatus}:* Job *${env.JOB_NAME}* Build #${env.BUILD_NUMBER}
                    👤 *Started by:* ${buildUser}
                    🔗 *Build URL:* <${buildUrl}|Click Here for Details>"""
                )
                echo "📦 Check your mail notif "
               // emailext (
                //subject: "Pipeline ${buildStatus}: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                //body: """
                   // <p>Youtube Link :- https://www.youtube.com/@devopsHarishNShetty </p>                                     
                   // <p>Maven App-tier DevSecops CICD pipeline status.</p>
                   // <p>Project: ${env.JOB_NAME}</p>
                   // <p>Build Number: ${env.BUILD_NUMBER}</p>
                   // <p>Build Status: ${buildStatus}</p>
                   // <p>Started by: ${buildUser}</p>
                   // <p>Build URL: <a href="${env.BUILD_URL}">${env.BUILD_URL}</a></p>
                //""",
               // to: 'unknownchapo0@gmail.com',
                //from: 'unknownchapo0@gmail.com',
                //mimeType: 'text/html',
                //attachmentsPattern: 'trivyfs.txt,trivy-image.json,trivy-image.txt,dependency-check-report.xml,zap_report.html,zap_report.json'
                //    )
            }
        }
    }

}

