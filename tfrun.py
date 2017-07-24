#!/usr/bin/python3
"""This script is a wrapper around terraform in order to help
enforce some 'guardrails' for the user to prevent accidents (e.g. accidental
'terraform apply' on production, etc.

Setup:
1 - Terraform dir structure with sep directory for each env you are managing:

    -production
    -testing
        -tfvars.tf (contains our magic string - see below)
        -main.tf
        -etc...
    -development
    -staging
    -global

2 - Create local vars file in each env directory (which you are probably already doing)
3 - Add the followingf magic string to the directory. The magic string should look like this for
    "testing" environment (kv) - specified as the first line in the local env vars file tfvars.tf
    If you wish to use a different name than 'tfvars.tf' just change the global var below.

"#environment|testing"

Example 'tfvars.tf':
------------------------------------
#environment|testing
# !!! leave line above as is - do not delete (used in our tfwrapper for our sanity checks) !!!
#
###############
# VARIABLES - local for testing env
###############
# Define whatever terraform vars you normally have here...blah blah

------------------------------------

4 - Adjust the path to your terraform binary to suit your environment.  I like to remove
    terraform from my profile path and add this script in its place to avoid
    'memory muscle' accidents :)
5 - Enjoy!
BJP 7/11/17"""

import argparse
import os
from subprocess import call
from enum import Enum
from pathlib import Path

class Environment(Enum):
    """ Environment enumeration"""
    INVALID = 0
    TESTING = 1
    DEVELOPMENT = 2
    STAGING = 3
    PRODUCTION = 4

# TODO
# --dump to local plan then execute that plan only for extra safety...
# (this is supposed to happen natively in TF .10, probably not going to bother with this)
#
# alias tfplan='terraform plan -out=.tfplan -refresh=false'
# alias tffreshplan='terraform plan -out=.tfplan'
# alias tfapply='terraform apply .tfplan; rm .tfplan'
# TODO
# The following ideas stolen from another engineers blogpost - sounds like a good thing
# to implement so capturing here:
# ----
# We are already using our continuous integration tool to validate the Terraform configuration.
# For now this just runs terraform validate, which checks for syntax errors.
# The next step we want to work towards is having our continuous integration run terraform plan
# and post the infrastructure changes as a comment in code review. The CI system would automatically
# run terraform apply when the change is approved. This removes a manual step, while also providing
# a more consistent audit trail of changes in the review comments. Terraform Enterprise has a
# feature like this, and we will be taking a look at it.


# Adjust these as needed
#
# The magic string is in this local vars file - see above for explanation
AFILE = "variables.tf"
# Path to terraform binary - include the trailing slash
TERRAFORMPATH = "/home/brianprovenzano/terraform/"


def Main():
    """ Main()"""
    parser = argparse.ArgumentParser(prog='tfrun')
    parser.add_argument("action", type=str, help="Terraform action to take " \
                        "(e.g. 'plan', 'apply', 'destroy', 'get-update', 'validate', " \
                        "'removeplanfile')")
    parser.add_argument("-y", "--yes", action="store_true", help="suppress " \
                        "confirmation of current working terraform " \
                        "environment (quiet mode). Possible Danger Will Robinson!!")
    parser.add_argument("-v", "--version", action='version', version='%(prog)s 1.4 (Custom " \
                        "wrapper for calling Hashicorp Terraform)')
    args = parser.parse_args()
    terraformAction = args.action.lstrip()


    try:
        # check the environment first
        currentEnvironment = CheckEnvironment(AFILE)
        # Run the action requested
        if terraformAction == "plan":
            action = terraformAction.upper()
            if args.yes:
                DisplayAction(action,currentEnvironment)
                RunTerraformPlan()
            else:
                answer = input(PromptQuestion(action, currentEnvironment))
                answer = True if answer.lstrip() == 'yes' else False
                if answer:
                    DisplayAction(action,currentEnvironment)
                    RunTerraformPlan()
        elif terraformAction == "apply":
            action = terraformAction.upper()
            if args.yes:
                DisplayAction(action,currentEnvironment)
                RunTerraformApply()
            else:
                answer = input(PromptQuestion(action, currentEnvironment))
                answer = True if answer.lstrip() == 'yes' else False
                if answer:
                    DisplayAction(action,currentEnvironment)
                    RunTerraformApply()
        elif terraformAction == "destroy":
            action = terraformAction.upper()
            if args.yes:
                DisplayAction(action,currentEnvironment)
                RunTerraformDestroy()
            else:
                answer = input(PromptQuestion(action, currentEnvironment))
                answer = True if answer.lstrip() == 'yes' else False
                if answer:
                    DisplayAction(action,currentEnvironment)
                    RunTerraformDestroy()
        elif terraformAction == "get-update":
            action = terraformAction.upper()
            if args.yes:
                DisplayAction(action,currentEnvironment)
                RunTerraformGetUpdate()
            else:
                answer = input(PromptQuestion(action, currentEnvironment))
                answer = True if answer.lstrip() == 'yes' else False
                if answer:
                    DisplayAction(action,currentEnvironment)
                    RunTerraformGetUpdate()
        elif terraformAction == "validate":
            action = terraformAction.upper()
            # Skip on validate - its safe
            DisplayAction(action,currentEnvironment)
            RunTerraformValidate()
        elif terraformAction == "removeplanfile":
            action = terraformAction.upper()
            DisplayAction(action,currentEnvironment)
            RemoveTFPlanFile()
        else:
            print("You must enter either 'apply', 'plan' "
                  "'destroy', 'removeplanfile', 'validate' or 'get-update'. "
                  "Other options are not supported at this time")
    except ValueError as ve:
        print(str(ve))
    except FileNotFoundError as fe:
        print("The file not found - REASON [{0}] \n"
              "Check your current environment directory for the correctly "
              "formatted local env tfvars.tf file and ensure terraform "
              "is located in the directory specified in this script."
              "It is also possible that you may not have the correct "
              "format for the magic string on the first line of the vars file. "
              "See this script's source code for details on "
              "creating one if needed.".format(fe))
    except Exception as e:
            print("Unknown error - REASON: {0}".format(e))


def CheckEnvironment(afile):
    """ Check the current terraform environment for sanity"""
    # 1 - Check the current directory we are in ('pwd' like)
    # 2 - Check the first line in the local tfvars.tf file for our magic env string (must be setup
    #     previously per design)
    # 3 - These (2) checks enforce sanity on what env we are operating on

    line = ""
    value = Environment.INVALID
    currentWorkingDirectory = os.path.basename(os.getcwd())

    with open(afile, "r") as f:
        alist = f.readline().strip().split("|")
        if len(alist) == 2:
            line = alist[1]
            if (line == "testing") and (currentWorkingDirectory == "testing"):
                value = Environment.TESTING
            elif (line == "development") and (currentWorkingDirectory == "development"):
                value = Environment.DEVELOPMENT
            elif (line == "staging") and (currentWorkingDirectory == "staging"):
                value = Environment.STAGING
            elif (line == "production") and (currentWorkingDirectory == "production"):
                value = Environment.PRODUCTION
            else:
                raise ValueError("The environment cannot be determined from tfvars file!! "
                "Likely invalid format for magic string "
                "on first line of local env tfvars.tf file OR in an invalid/unknown current "
                "working directory (environment) for the terraform project")
        else:
            raise ValueError("The environment cannot be determined from tfvars file!! "
                             "Likely invalid format for magic string on first line of "
                             "local env tfvars.tf file.")

    return value


def PromptQuestion(TFAction, env):
    """ Prompt user with current env to perform tf action on"""
    question = "\n {1} selected!!: Are you sure you wish to run " \
               "'terraform {0}' on the {1} environment?: ".format(TFAction, env.name)
    return question


def DisplayAction(TFAction, env):
    """ Run action info message"""
    message = "\n {1} selected!!: Running  " \
               "'terraform {0}' on the {1} environment! ".format(TFAction, env.name)
    return message


def RunTerraformPlan():
    """ Wraps up a 'terraform plan' call"""
    # TODO - entry point for saving what was planned to git for tracking??
    # call get always before a plan as it is safe and will include new modules if present
    call([(TERRAFORMPATH + "terraform"), "get"])
    previousPlan = Path(".tfplan")
    if previousPlan.is_file():
        previousPlan.unlink()
    call([(TERRAFORMPATH + "terraform"), "plan", "-out=.tfplan"])


def RunTerraformGetUpdate():
    """ Wraps up a 'terraform get -update' call"""
    # TODO - entry point for saving what was planned to git for tracking??
    # will check for changes to currently included modules and include them in the plan/apply
    call([(TERRAFORMPATH + "terraform"), "get", "-update"])


def RunTerraformValidate():
    """ Wraps up a 'terraform validate' call"""
    # validates tf syntax before a plan/apply
    call([(TERRAFORMPATH + "terraform"), "validate"])


def RemoveTFPlanFile():
    """ Remove a plan file if you don't plan on applying (pun intended ;))"""
    previousPlan = Path(".tfplan")
    if previousPlan.is_file():
        previousPlan.unlink()
        print("\n Removed previous local terraform plan file!!")


def RunTerraformApply():
    """ Wraps up a 'terraform apply' call"""
    # TODO - entry point for saving what was applied to git for tracking??
    previousPlan = Path(".tfplan")
    if previousPlan.is_file():
        call([(TERRAFORMPATH + "terraform"), "apply .tfplan"])
        previousPlan.unlink()
    else:
        raise ValueError("Cannot find a .tfplan file!! Did you run 'plan' before "
                "this 'apply'?")

def RunTerraformDestroy():
    """ Wraps up a 'terraform destroy' call"""
    # TODO - entry point for saving what was destroyed to git for tracking??
    call([(TERRAFORMPATH + "terraform"), "destroy"])


if __name__ == '__main__':
    Main()
