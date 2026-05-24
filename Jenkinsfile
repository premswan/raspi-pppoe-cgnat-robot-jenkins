pipeline {
    agent any

    parameters {
        string(name: 'RPI_HOST', defaultValue: '192.168.1.2', description: 'Raspberry Pi IP address')
        string(name: 'RPI_USER', defaultValue: 'pi', description: 'Raspberry Pi SSH username')
        string(name: 'IFACE', defaultValue: 'eth0', description: 'Interface on Raspberry Pi for tcpdump')
        string(name: 'CAPTURE_SECONDS', defaultValue: '20', description: 'tcpdump capture duration')
        string(name: 'PACKET_COUNT', defaultValue: '30', description: 'Maximum packet count')
        booleanParam(name: 'USE_SAMPLE', defaultValue: false, description: 'Use sample tcpdump file instead of Raspberry Pi')
    }

    environment {
        VENV_DIR = "${WORKSPACE}/.venv"
        RESULTS_DIR = "${WORKSPACE}/results"
    }

    stages {
        stage('Checkout from GitHub') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Python Environment') {
            steps {
                sh '''
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Check Raspberry Pi SSH') {
            when {
                expression { return params.USE_SAMPLE == false }
            }
            steps {
                sshagent(credentials: ['raspi-ssh-key']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no ${RPI_USER}@${RPI_HOST} "hostname && which tcpdump && which timeout"
                    '''
                }
            }
        }

        stage('Run Robot PPPoE CGNAT Test') {
            steps {
                script {
                    if (params.USE_SAMPLE) {
                        sh '''
                            . ${VENV_DIR}/bin/activate
                            robot -d ${RESULTS_DIR} \
                              --variable USE_SAMPLE:True \
                              tests/pppoe_cgnat_validation.robot
                        '''
                    } else {
                        sshagent(credentials: ['raspi-ssh-key']) {
                            sh '''
                                . ${VENV_DIR}/bin/activate
                                robot -d ${RESULTS_DIR} \
                                  --variable RPI_HOST:${RPI_HOST} \
                                  --variable RPI_USER:${RPI_USER} \
                                  --variable IFACE:${IFACE} \
                                  --variable CAPTURE_SECONDS:${CAPTURE_SECONDS} \
                                  --variable PACKET_COUNT:${PACKET_COUNT} \
                                  tests/pppoe_cgnat_validation.robot
                            '''
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/**', allowEmptyArchive: true

            // Requires Jenkins Robot Framework plugin.
            // If plugin is not installed, this block may fail.
            // Remove this block if you only want archived log.html/report.html.
            robot outputPath: 'results',
                  outputFileName: 'output.xml',
                  reportFileName: 'report.html',
                  logFileName: 'log.html',
                  passThreshold: 100.0,
                  unstableThreshold: 0.0
        }
    }
}
