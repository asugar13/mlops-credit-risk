// Jenkinsfile — Postgres batch scoring (renewals >= 11 months)
// Uses venv + psycopg v3 (binary wheels; no pg_config needed)

pipeline {
  agent any

  triggers {
    cron('H 2 * * *')   // daily at ~02:00
  }

  environment {
    DB_HOST = 'postgres'           // docker service name or resolvable hostname
    DB_PORT = '5432'
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
          python3 --version
          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('Run batch scoring') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'pg-cred',
          usernameVariable: 'DB_USER',
          passwordVariable: 'DB_PASSWORD'
        )]) {
          sh '''
            set -e
            . .venv/bin/activate
            python3 batch_score.py
          '''
        }
      }
    }
  }

  post {
    always {
      cleanWs()
    }
  }
}
