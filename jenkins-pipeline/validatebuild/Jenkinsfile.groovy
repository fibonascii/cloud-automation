#!/usr/bin/env groovy

import hudson.model. *
import hudson.EnvVars
import groovy.json.JsonSlurperClassic
import groovy.json.JsonBuilder
import groovy.json.JsonOutput
import java.net.URL

def emailFailure() {
    mail(
        to: 'dpreble@brierley.com',
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
        
        def EXECUTE_IMAGE_BUILD=params.EXECUTE_IMAGE_BUILD
        echo "Execute Image Build: ${EXECUTE_IMAGE_BUILD}"
        
        def EXECUTE_PERFORMANCE_TEST=params.EXECUTE_PERFORMANCE_TEST
        echo "Execute Performance Test: ${EXECUTE_PERFORMANCE_TEST}"

        def TEAR_DOWN_ENVIRONMENT=params.TEAR_DOWN_ENV_DEFAULT
        echo "Tear Down Environment on User Input Timeout: ${TEAR_DOWN_ENV_DEFAULT}"
        
        echo "Branch Specifier: ${BRANCH_SPECIFIER}"
        // Clone Repository
        git branch: "${BRANCH_SPECIFIER}",
            credentialsId: 'cd3283c2-6d74-4a60-9631-e81e5ddeb439',
            url: 'https://github.com/brierley/cloud-automation.git'

        // Build Image With Packer and Generate Build Manifest
        stage("Build Image") {
            dir("packer/builds/${PROCEDURE}") {
                try {
                    if (EXECUTE_IMAGE_BUILD)
		    {
                    sh "packer.io build -force -var-file ../../../jenkins-pipeline/validatebuild/vars_file.json ${PROCEDURE}.json"
		    }
                    else
                    {
                    echo "Image Build not Requested"
                    }
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
                    if (fileExists("../../jenkins-pipeline/validatebuild/manifest.json")) {
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
     }   

    // Execute Performance Test via Jmeter
        stage("Execute Performance Test") {
            dir("jenkins-pipeline/validatebuild") {
                try {
                if (EXECUTE_PERFORMANCE_TEST)
		   {
                    sh "python3 get_parameters.py -p ${PROCEDURE} -e ${ENVIRONMENT}"
                   }
                 else
                   {
                   echo "Performance Test not Requested"
                   }
                }
                catch(exc) {
                    error("Executing Performance Test Failed.")
                    throw exc
                    emailFailiure()
                }
            }
        }

      // Get User Input on Environment Tear Down
        stage("User Input on: Tear Down Temporary Environment") {
                try {
                timeout(time:60, unit:'MINUTES') {
                TEAR_DOWN_ENVIRONMENT = input(
        id: 'Proceed1', message: 'Select CheckBox to Tear Down Temporary Environment', parameters: [
        [$class: 'BooleanParameterDefinition', defaultValue: false, description: 'Select Checkbox to Tear Down Environment', name: 'Mark Checkbox to Tear down Environment']
        ])
                echo "User selected ${TEAR_DOWN_ENVIRONMENT} in regards to Tearing down the Environment." 
		}
		}
                catch(exc) {
		    // timeout reached or input Aborted
                    def error_user = exc.getCauses()[0].getUser()
                        if('SYSTEM' == error_user.toString()) { // SYSTEM means timeout
                            echo ("Input timeout expired for Tear Down Environment Selection, default response will be used: " + TEAR_DOWN_ENVIRONMENT)
                        } else {
                            echo "Input aborted by: [${error_user}]"
                            error("Pipeline aborted by: [${error_user}]")
                            throw exc
			    emailFailure()
                        }
                }
            }
    
      // Tear down Environment
        stage("Tear down environment") {
            dir("cloudformation/${PROCEDURE}") {
                try {
                    if(TEAR_DOWN_ENVIRONMENT)
	            {
                      sh "sceptre delete-env ${ENVIRONMENT}"
		    }
                }
                catch(exc) {
                    error("Deleting Environment Failed.")
                    throw exc
                    emailFailiure()
                }
            }
        }

}
