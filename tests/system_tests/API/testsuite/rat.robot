*** Settings ***
# For more detail init setting, please refer to ../res/init.robot
Resource         ../res/init.robot
Test Timeout     ${TEST_API_TIMEOUT}

# For more detail init setting, please refer to ../res/valueset.robot
Suite Setup       Run Keywords      Get Test Value    stag
# Timeout Period: 5 sec, Retry Period: 3 sec,
                  ...               AND    Wait Until Keyword Succeeds    5s     3s    Check Service Is Ready
Suite Setup       Get Test Value     prod
Suite Teardown    Release Test Value


*** Test Cases ***
# todo