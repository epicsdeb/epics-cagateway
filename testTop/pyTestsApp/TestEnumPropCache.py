#!/usr/bin/env python
import os
import unittest
import epics
from epics import ca, dbr
import IOCControl
import GatewayControl
import gwtests
import time
import subprocess

class TestEnumPropertyCache(unittest.TestCase):
    '''Testing the Gateway PV property cache for ENUM type data (list of state strings)
    Set up a connection through the Gateway - change a property externally - check if Gateway cache was updated
    Detects EPICS bug lp:1510955 (https://bugs.launchpad.net/epics-base/+bug/1510955)
    '''

    def connectGwStats(self):
        self.gw_vctotal = ca.create_channel("gwtest:vctotal")
        self.gw_pvtotal = ca.create_channel("gwtest:pvtotal")
        self.gw_connected = ca.create_channel("gwtest:connected")
        self.gw_active = ca.create_channel("gwtest:active")
        self.gw_inactive = ca.create_channel("gwtest:inactive")

    def updateGwStats(self):
        self.vctotal = ca.get(self.gw_vctotal)
        self.pvtotal = ca.get(self.gw_pvtotal)
        self.connected = ca.get(self.gw_connected)
        self.active = ca.get(self.gw_active)
        self.inactive = ca.get(self.gw_inactive)


    def setUp(self):
        gwtests.setup()
        self.iocControl = IOCControl.IOCControl()
        self.gatewayControl = GatewayControl.GatewayControl()
        self.iocControl.startIOC()
        self.gatewayControl.startGateway()
        self.propSupported = False
        os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
        os.environ["EPICS_CA_ADDR_LIST"] = "localhost:{0} localhost:{1}".format(gwtests.iocPort,gwtests.gwPort)
        ca.initialize_libca()

        # Check if IOC supports DBE_PROPERTY
        self.eventsReceivedIOC = 0
        ioc = epics.PV("ioc:passive0", auto_monitor=epics.dbr.DBE_PROPERTY)
        ioc.add_callback(self.onChangeIOC)
        ioc.get()
        pvhigh = epics.PV("ioc:passive0.HIGH", auto_monitor=None)
        pvhigh.put(18.0, wait=True)
        time.sleep(.05)
        if self.eventsReceivedIOC == 2:
            self.propSupported = True
        ioc.disconnect()
        self.connectGwStats()

    def tearDown(self):
        ca.finalize_libca()
        self.gatewayControl.stop()
        self.iocControl.stop()

    def onChangeIOC(self, pvname=None, **kws):
        self.eventsReceivedIOC += 1

    def onChange(self, pvname=None, **kws):
        a = 1


    def testEnumPropCache_ValueMonitorCTRLget(self):
        '''Monitor PV (value events) through GW - change ENUM string directly - get the DBR_CTRL of the PV through GW'''
        # gateway should show no VC (client side connection) and no PV (IOC side connection)
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 0, "Expected GW PV total count: 0, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 0, "Expected GW connected PV count: 0, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # enumtest is an mbbi record with three strings defined: zero one two
        gw = ca.create_channel("gateway:enumtest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        (gw_cbref, gw_uaref, gw_eventid) = ca.create_subscription(gw, mask=dbr.DBE_VALUE, callback=self.onChange)
        ioc = ca.create_channel("ioc:enumtest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))
        (ioc_cbref, ioc_uaref, ioc_eventid) = ca.create_subscription(ioc, mask=dbr.DBE_VALUE, callback=self.onChange)

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # enum string should not have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        oneStr = ioc_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'one', "Expected IOC enum[1]: one; actual enum[1]: "+ oneStr)
        gw_ctrl = ca.get_ctrlvars(gw)
        oneStr = gw_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'one', "Expected GW enum[1]: one; actual enum[1]: "+ oneStr)

        # set enum string on IOC
        ioc_enum1 = ca.create_channel("ioc:enumtest.ONST")
        ca.put(ioc_enum1, 'uno', wait=True)
        time.sleep(.1)

        # Now the enum string should have been updated (if IOC supports DBE_PROPERTY)
        ioc_ctrl = ca.get_ctrlvars(ioc)
        oneStr = ioc_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'uno', "Expected IOC enum[1]: uno; actual enum[1]: "+ oneStr)
        if self.propSupported:
            gw_expected = 'uno'
        else:
            gw_expected = 'one'
        gw_ctrl = ca.get_ctrlvars(gw)
        oneStr = gw_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == gw_expected, "Expected GW enum[1]: {0}; actual enum[1]: {1}".format(gw_expected, oneStr))


    def testEnumPropCache_ValueGetCTRLGet(self):
        '''Get PV (value) through GW - change ENUM string directly - get the DBR_CTRL of the PV through GW'''
        # gateway should show no VC (client side connection) and no PV (IOC side connection)
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 0, "Expected GW PV total count: 0, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 0, "Expected GW connected PV count: 0, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # enumtest is an mbbi record with three strings defined: zero one two
        gw = ca.create_channel("gateway:enumtest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        ioc = ca.create_channel("ioc:enumtest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # enum string should not have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        oneStr = ioc_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'one', "Expected IOC enum[1]: one; actual enum[1]: "+ oneStr)
        gw_ctrl = ca.get_ctrlvars(gw)
        oneStr = gw_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'one', "Expected GW enum[1]: one; actual enum[1]: "+ oneStr)

        # set enum string on IOC
        ioc_enum1 = ca.create_channel("ioc:enumtest.ONST")
        ca.put(ioc_enum1, 'uno', wait=True)
        time.sleep(.1)

        # Now the enum string should have been updated (if IOC supports DBE_PROPERTY)
        ioc_ctrl = ca.get_ctrlvars(ioc)
        oneStr = ioc_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'uno', "Expected IOC enum[1]: uno; actual enum[1]: "+ oneStr)
        if self.propSupported:
            gw_expected = 'uno'
        else:
            gw_expected = 'one'
        gw_ctrl = ca.get_ctrlvars(gw)
        oneStr = gw_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == gw_expected, "Expected GW enum[1]: {0}; actual enum[1]: {1}".format(gw_expected, oneStr))


    def testEnumPropCache_ValueGetDisconnectCTRLGet(self):
        '''Get PV (value) through GW - disconnect client - change ENUM string directly - get the DBR_CTRL of the PV through GW'''
        # gateway should show no VC (client side connection) and no PV (IOC side connection)
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 0, "Expected GW PV total count: 0, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 0, "Expected GW connected PV count: 0, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # enumtest is an mbbi record with three strings defined: zero one two
        gw = ca.create_channel("gateway:enumtest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        ioc = ca.create_channel("ioc:enumtest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # enum string should not have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        oneStr = ioc_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'one', "Expected IOC enum[1]: one; actual enum[1]: "+ oneStr)
        gw_ctrl = ca.get_ctrlvars(gw)
        oneStr = gw_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'one', "Expected GW enum[1]: one; actual enum[1]: "+ oneStr)

        # disconnect Channel Access, reconnect Gateway stats
        ca.finalize_libca()
        ca.initialize_libca()
        self.connectGwStats()

        # gateway should show no VC and 1 connected inactive PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 1, "Expected GW inactive PV count: 1, actual: " + str(self.inactive))

        # set enum string on IOC
        ioc_enum1 = ca.create_channel("ioc:enumtest.ONST")
        ca.put(ioc_enum1, 'uno', wait=True)
        time.sleep(.1)

        # reconnect Gateway and IOC
        gw = ca.create_channel("gateway:enumtest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        ioc = ca.create_channel("ioc:enumtest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # Now the enum string should have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        oneStr = ioc_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'uno', "Expected IOC enum[1]: uno; actual enum[1]: "+ oneStr)
        gw_ctrl = ca.get_ctrlvars(gw)
        oneStr = gw_ctrl['enum_strs'][1]
        self.assertTrue(oneStr == 'uno', "Expected GW enum[1]: uno; actual enum[1]: "+ oneStr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
