
# PLEASE READ DISCLAIMER
#
#    This is a sample script for demo and reference purpose only.
#    It is subject to change for content updates without warning.
#
# REQUIREMENTS
#    - Python modules: requests
#
# SUPPORTS
#    - Python 2.7 and 3+
#    - IxNetwork API servers: Windows, WindowsConnectionMgr and Linux
#
# DESCRIPTION
#    This sample script demonstrates:
#        - REST API configurations using two back-to-back Ixia ports.
#        - Connecting to Windows IxNetwork API server or Linux API server.
#
#        - Verify for sufficient amount of port licenses before testing.
#        - Verify port ownership.
#        - Configure two IPv6/BGP Topology Groups
#        - Start protocols
#        - Verify BGP protocol sessions
#        - Create an IPv6 Traffic Item
#        - Apply Traffic
#        - Start Traffic
#        - Get stats
#
# USAGE
#    python <script>.py windows
#    python <script>.py linux

import re, sys, os, traceback

# These  modules are one level above.
sys.path.insert(0, (os.path.dirname(os.path.abspath(__file__).replace('SampleScripts', 'Modules'))))
from IxNetRestApi import *
from IxNetRestApiPortMgmt import PortMgmt
from IxNetRestApiTraffic import Traffic
from IxNetRestApiProtocol import Protocol
from IxNetRestApiStatistics import Statistics

# Default the API server to either windows or linux.
osPlatform = 'windows'

try:
    #---------- Preference Settings --------------

    forceTakePortOwnership = True
    releasePortsWhenDone = False
    enableDebugTracing = True
    deleteSessionAfterTest = False ;# For Windows Connection Mgr and Linux API server only

    licenseServerIp = '172.16.101.3'
    licenseModel = 'subscription'

    ixChassisIp = '172.16.102.5'
    # [chassisIp, cardNumber, slotNumber]
    portList = [[ixChassisIp, '1', '1'], [ixChassisIp, '1', '2']]

    if osPlatform == 'linux':
        mainObj = Connect(apiServerIp='172.16.102.2',
                          serverIpPort='443',
                          username='admin',
                          password='admin',
                          deleteSessionAfterTest=deleteSessionAfterTest,
                          verifySslCert=False,
                          serverOs=osPlatform,
                          generateLogFile='ixiaDebug.log',
                          traceLevel='all'
                          )

    if osPlatform in ['windows', 'windowsConnectionMgr']:
        mainObj = Connect(apiServerIp='172.16.101.3',
                          serverIpPort='11009',
                          serverOs=osPlatform,
                          deleteSessionAfterTest=True,
                          generateLogFile='ixiaDebug.log',
                          traceLevel='all'
                          )

    #---------- Preference Settings End --------------

    # Only need to blank the config for Windows because osPlatforms such as Linux and
    # Windows Connection Mgr supports multiple sessions and a new session always come up as a blank config.
    if osPlatform == 'windows':
        mainObj.newBlankConfig()

    mainObj.configLicenseServerDetails([licenseServerIp], licenseModel)
    portObj = PortMgmt(mainObj)
    portObj.assignPorts(portList, forceTakePortOwnership)

    protocolObj = Protocol(mainObj)
    topologyObj1 = protocolObj.createTopologyNgpf(portList=[portList[0]], topologyName='Topo1')

    deviceGroupObj1 = protocolObj.createDeviceGroupNgpf(topologyObj1,
                                                        multiplier=1,
                                                        deviceGroupName='DG1')
                                                  
    topologyObj2 = protocolObj.createTopologyNgpf(portList=[portList[1]], topologyName='Topo2')

    deviceGroupObj2 = protocolObj.createDeviceGroupNgpf(topologyObj2,
                                                        multiplier=1,
                                                        deviceGroupName='DG2')

    ethernetObj1 = protocolObj.configEthernetNgpf(deviceGroupObj1,
                                                  ethernetName='MyEth1',
                                                  macAddress={'start': '00:01:01:00:00:01',
                                                              'direction': 'increment',
                                                              'step': '00:00:00:00:00:01'},
                                                  macAddressPortStep='disabled',
                                                  vlanId={'start': 103,
                                                          'direction': 'increment',
                                                          'step':0})

    ethernetObj2 = protocolObj.configEthernetNgpf(deviceGroupObj2,
                                                  ethernetName='MyEth2',
                                                  macAddress={'start': '00:01:02:00:00:01',
                                                              'direction': 'increment',
                                                              'step': '00:00:00:00:00:01'},
                                                  macAddressPortStep='disabled',
                                                  vlanId={'start': 103,
                                                          'direction': 'increment',
                                                          'step':0})

    ipv6Obj1 = protocolObj.configIpv6Ngpf(ethernetObj1,
                                          ipv6Address={'start': '2001:0:0:1:0:0:0:1',
                                                       'direction': 'increment',
                                                       'step': '0:0:0:0:0:0:0:1'},
                                          ipv6AddressPortStep='disabled',
                                          gateway={'start': '2001:0:0:1:0:0:0:2',
                                                   'direction': 'increment',
                                                   'step': '0:0:0:0:0:0:0:0'},
                                          gatewayPortStep='disabled',
                                          prefix=64,
                                          resolveGateway=True)

    ipv6Obj2 = protocolObj.configIpv6Ngpf(ethernetObj2,
                                          ipv6Address={'start': '2001:0:0:1:0:0:0:2',
                                                       'direction': 'increment',
                                                       'step': '0:0:0:0:0:0:0:1'},
                                          ipv6AddressPortStep='disabled',
                                          gateway={'start': '2001:0:0:1:0:0:0:1',
                                                   'direction': 'increment',
                                                   'step': '0:0:0:0:0:0:0:0'},
                                          gatewayPortStep='disabled',
                                          prefix=64,
                                          resolveGateway=True)

    bgpObj1 = protocolObj.configBgpIpv6(ipv6Obj1,
                                        name = 'bgp_1',
                                        active = True,
                                        holdTimer = 90,
                                        dutIp={'start': '2001:0:0:1:0:0:0:2', 'direction': 'increment', 'step': '0:0:0:0:0:0:0:0'},
                                        localAs2Bytes = 101,
                                        enableGracefulRestart = False,
                                        restartTime = 45,
                                        type = 'internal',
                                        enableBgpIdSameasRouterId = True)
    
    bgpObj2 = protocolObj.configBgpIpv6(ipv6Obj2,
                                        name = 'bgp_2',
                                        active = True,
                                        holdTimer = 90,
                                        dutIp={'start': '2001:0:0:1:0:0:0:1', 'direction': 'increment', 'step': '0:0:0:0:0:0:0:0'},
                                        localAs2Bytes = 101,
                                        enableGracefulRestart = False,
                                        restartTime = 45,
                                        type = 'internal',
                                        enableBgpIdSameasRouterId = True)
    
    networkGroupObj1 = protocolObj.configNetworkGroup(create=deviceGroupObj1,
                                                      ipVersion='ipv6',
                                                      name='networkGroup1',
                                                      multiplier = 100,
                                                      networkAddress = {'start': '1000::1',
                                                                        'step': '0:0:0:0:0:0:0:1',
                                                                        'direction': 'increment'},
                                                      prefixLength = 64)

    networkGroupObj2 = protocolObj.configNetworkGroup(create=deviceGroupObj2,
                                                      ipVersion='ipv6',
                                                      name='networkGroup2',
                                                      multiplier = 100,
                                                      networkAddress = {'start': '1001::1',
                                                                        'step': '0:0:0:0:0:0:0:1',
                                                                        'direction': 'increment'},
                                                      prefixLength = 64)

    protocolObj.startAllProtocols()
    protocolObj.verifyProtocolSessionsUp()

    # For all parameter options, go to the API configTrafficItem.
    # mode = create or modify
    # Note: Check API configTrafficItem for options.
    trafficObj = Traffic(mainObj)
    trafficStatus = trafficObj.configTrafficItem(
        mode='create',
        trafficItem = {
            'name': 'Topo1 to Topo2',
            'trafficType': 'ipv6',
            'biDirectional': True,
            'srcDestMesh': 'one-to-one',
            'routeMesh': 'oneToOne',
            'allowSelfDestined': False,
            'trackBy': ['flowGroup0', 'vlanVlanId0']},
        endpoints = [{'name': 'Flow-Group-1',
                      'sources': [topologyObj1],
                      'destinations': [topologyObj2]
                  }],
        # transmissionType:   fixedFrameCount|continuous
        # frameRateType:      percentLineRate|framesPerSecond
        # portDistribution:   applyRateToAll|splitRateEvenly
        # streamDistribution: splitRateEvenly|applyRateToAll
        configElements = [{'transmissionType': 'fixedFrameCount',
                           'frameCount': 50000,
                           'frameRate': 88,
                           'frameRateType': 'percentLineRate',
                           'frameSize': 128,
                           'portDistribution': 'applyRateToAll',
                           'streamDistribution': 'splitRateEvenly'
                       }])

    trafficItemObj   = trafficStatus[0]
    endpointObj      = trafficStatus[1][0]
    configElementObj = trafficStatus[2][0]

    trafficObj.startTraffic(regenerateTraffic=True, applyTraffic=True)

    # Check the traffic state before getting stats.
    #    Use one of the below APIs based on what you expect the traffic state should be before calling stats.
    #    'stopped': If you expect traffic to be stopped such as for fixedFrameCount and fixedDuration.
    #    'started': If you expect traffic to be started such as in continuous mode.
    trafficObj.checkTrafficState(expectedState=['stopped'], timeout=45)
    #trafficObj.checkTrafficState(expectedState=['started'], timeout=45)

    statObj = Statistics(mainObj)
    stats = statObj.getStats(viewName='Flow Statistics')

    print('\n{txPort:10} {txFrames:15} {rxPort:10} {rxFrames:15} {frameLoss:10}'.format(
        txPort='txPort', txFrames='txFrames', rxPort='rxPort', rxFrames='rxFrames', frameLoss='frameLoss'))
    print('-'*90)

    for flowGroup,values in stats.items():
        txPort = values['Tx Port']
        rxPort = values['Rx Port']
        txFrames = values['Tx Frames']
        rxFrames = values['Rx Frames']
        frameLoss = values['Frames Delta']

        print('{txPort:10} {txFrames:15} {rxPort:10} {rxFrames:15} {frameLoss:10} '.format(
            txPort=txPort, txFrames=txFrames, rxPort=rxPort, rxFrames=rxFrames, frameLoss=frameLoss))

    if releasePortsWhenDone == True:
        portObj.releasePorts(portList)

    if osPlatform == 'linux':
        mainObj.linuxServerStopAndDeleteSession()

    if osPlatform == 'windowsConnectionMgr':
        mainObj.deleteSession()

except (IxNetRestApiException, Exception, KeyboardInterrupt) as errMsg:
    if enableDebugTracing:
        if not bool(re.search('ConnectionError', traceback.format_exc())):
            print('\n%s' % traceback.format_exc())

    if 'mainObj' in locals() and osPlatform == 'linux':
        if deleteSessionAfterTest:
            mainObj.linuxServerStopAndDeleteSession()

    if 'mainObj' in locals() and osPlatform in ['windows', 'windowsConnectionMgr']:
        if releasePortsWhenDone and forceTakePortOwnership:
            portObj.releasePorts(portList)

        if osPlatform == 'windowsConnectionMgr':
            if deleteSessionAfterTest:
                mainObj.deleteSession()
