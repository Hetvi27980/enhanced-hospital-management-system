pipeline {
  agent any
  stages {
    stage('Plan Stage') {
      steps {
        powershell 'echo "Compiling"'
      }
    }

    stage('Code Stage') {
      steps {
        powershell 'echo "Coding"'
      }
    }

    stage('Build Stage') {
      steps {
        powershell 'echo "Building"'
      }
    }

  }
}