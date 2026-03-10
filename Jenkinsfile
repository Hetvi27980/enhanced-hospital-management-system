pipeline {
  agent any
  stages {
    stage('Plan Stage') {
      steps {
        powershell 'Echo"Compiling"'
        powershell 'Encoding"Compiling"'
      }
    }

    stage('Code Stage') {
      steps {
        powershell 'echo"Coding"'
      }
    }

    stage('Build Stage') {
      steps {
        powershell 'echo"Building"'
      }
    }

  }
}