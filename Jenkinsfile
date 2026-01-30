// Jenkinsfile — simple daily batch scoring for renewals (>= 11 months)
// Assumptions:
// - Repo contains: batch_score.py + requirements.txt
// - Jenkins has Python 3 installed on the agent
// - You created a Jenkins credential (Username/Password) with ID: mariadb-cred
// - MariaDB is reachable from the Jenkins agent

pipeline {
  agent any

  triggers {
    // Run once per day at a stable, hashed minute past 02:00
    cron('H 2 * * *')
  }

  environment {
    DB_HOST = 'mariadb.your.internal.host'   // <-- change
    DB_PORT = '3306'
    DB_NAME = 'insurance_pricing'
    MODEL_VERSION = 'mock-renewal-v1'
    PYTHONUNBUFFERED = '1'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Set up Python venv') {
      steps {
        sh '''
          set -e
          python3 -m venv .venv
          . .venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('Run batch scoring') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'mariadb-cred',
          usernameVariable: 'DB_USER',
          passwordVariable: 'DB_PASSWORD'
        )]) {
          sh '''
            set -e
            . .venv/bin/activate
            python batch_score.py
          '''
        }
      }
    }
  }

  post {
    always {
      // If you later add logs/artifacts, you can archive them here
      // archiveArtifacts artifacts: 'logs/**', allowEmptyArchive: true
      cleanWs()
    }
  }
}
