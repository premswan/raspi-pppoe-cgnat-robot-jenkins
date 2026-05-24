*** Settings ***
Documentation       Capture PPPoE packets from Raspberry Pi and validate source IP is inside CGNAT range 100.64.0.0/10.
Library             ../resources/PppoeCgnatLibrary.py

Suite Setup         Log Test Environment


*** Variables ***
${RPI_HOST}             192.168.1.2
${RPI_USER}             pi
${SSH_KEY}              ${EMPTY}
${IFACE}                eth0
${CAPTURE_SECONDS}      20
${PACKET_COUNT}         30
${USE_SAMPLE}           False
${SAMPLE_FILE}          ${CURDIR}/../sample/sample_tcpdump.txt
${CGNAT_NETWORK}        100.64.0.0/10


*** Test Cases ***
Validate PPPoE Source IP Belongs To CGNAT Range
    [Documentation]    Captures PPPoE packets and validates that at least one packet source IP belongs to 100.64.0.0/10.
    ${tcpdump_output}=    Get Tcpdump Output
    Log    ${tcpdump_output}
    ${flows}=    Extract PPPoE IP Flows    ${tcpdump_output}
    Should Not Be Empty    ${flows}    No PPPoE IP flow was parsed from tcpdump output.
    ${matching_flows}=    Get Flows With Source IP In Network    ${flows}    ${CGNAT_NETWORK}
    Should Not Be Empty    ${matching_flows}    No PPPoE packet source IP found inside ${CGNAT_NETWORK}.
    Log Matching Flows    ${matching_flows}


*** Keywords ***
Log Test Environment
    Log To Console    \nRunning PPPoE CGNAT validation
    Log To Console    Raspberry Pi: ${RPI_USER}@${RPI_HOST}
    Log To Console    Interface: ${IFACE}
    Log To Console    CGNAT Network: ${CGNAT_NETWORK}

Get Tcpdump Output
    IF    '${USE_SAMPLE}' == 'True'
        ${output}=    Read Sample Tcpdump File    ${SAMPLE_FILE}
    ELSE
        ${output}=    Capture Tcpdump From Raspberry
        ...    host=${RPI_HOST}
        ...    user=${RPI_USER}
        ...    iface=${IFACE}
        ...    seconds=${CAPTURE_SECONDS}
        ...    packet_count=${PACKET_COUNT}
        ...    ssh_key=${SSH_KEY}
    END
    RETURN    ${output}
