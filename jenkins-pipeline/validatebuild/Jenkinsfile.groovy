#!/usr/bin/env groovy

import hudson.model. *
import hudson.EnvVars
import groovy.json.JsonSlurperClassic
import groovy.json.JsonBuilder
import groovy.json.JsonOutput
import java.net.URL

def emailFailure() {
    mail(
        to: 'rkirby@brierley.com',
        from: 'no-reply@brierleyjenkins.com',
        replyTo: 'no-reply@brierleyjenkins.com',
        subject: "${BUILD_ID} Failure",
        body: "The build ${BUILD_ID} Failed"
    )
}

node {
        // Get Build ID
        def BUILD_ID=env.BUILD_ID
        echo "Current Build: ${BUILD_ID}"

        // Set Parameter Variables
        def PROCEDURE=params.PROCEDURE
        echo "Procedure: ${PROCEDURE}"

        def ENVIRONMENT=params.ENVIRONMENT
        echo "Environment: ${ENVIRONMENT}"

        // Clone Repository
        git branch: 'task/LW-7501',
            credentialsId: 'bf894a98-07e7-449a-8c35-2627eab42a5e',
            url: 'https://github.com/brierley/cloud-automation.git'

        // Build Image With Packer and Generate Build Manifest
        stage("Build Image") {
            dir("packer/builds/${PROCEDURE}") {
                try { 
                    sh "packer.io build -var-file ../../../jenkins-pipeline/validatebuild/vars_file.json ${PROCEDURE}.json"
                }
                catch(exc) {
                    error("Building Image Failed.")
                    throw exc
                    emailFailiure()
                }
            }
        }
        
        // Create Envrionemnt With CloudFormation
        stage('Create Environment') {
            dir("cloudformation/${PROCEDURE}") {
                try { 
                    if (fileExists("manifest.json")) {
                        echo "Manifest File Exists. Launching Environment"
                        sh "sceptre launch-env ${ENVIRONMENT}"
                    }
                    else {
                        error("Manfiest File Does Not Exist")
                    }
                }
                catch(exc) {
                    error("Environment Failed To Create")
                }
            }
           else {
            echo "Manifest file not present. Exiting"
        }
    }
}
