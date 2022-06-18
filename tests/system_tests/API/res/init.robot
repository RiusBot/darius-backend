*** Variable ***
${TEST_API_TIMEOUT}         65000ms
#${work_dir}                 ./tests/system_tests/API


*** Settings ***
Library           BuiltIn
Library           Collections
Library           DateTime
Library           ImapLibrary
Library           OperatingSystem
Library           Process
Library           RequestsLibrary
Library           String
Library           XML
Library           SeleniumLibrary
Library           JSONLibrary
Library           pabot.PabotLib

Resource          ../lib/keywords_init.robot
Resource          ../lib/keywords_util.robot
Resource          ../lib/keywords_prodcut_api.robot
Resource          ../lib/keywords_templates.robot