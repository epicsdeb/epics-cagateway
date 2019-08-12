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

class TestPropertyCache(unittest.TestCase):
    '''Testing the Gateway PV property cache
    Set up a connection through the Gateway - change a property externally - check if Gateway cache was updated
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

    def testPropCache_ValueMonitorCTRLget(self):
        '''Monitor PV (value events) through GW - change properties (HIGH, EGU) directly - get the DBR_CTRL of the PV through GW'''
        # gateway should show no VC (client side connection) and no PV (IOC side connection)
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 0, "Expected GW PV total count: 0, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 0, "Expected GW connected PV count: 0, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # gwcachetest is an ai record with full set of alarm limits: -100 -10 10 100
        gw = ca.create_channel("gateway:gwcachetest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        (gw_cbref, gw_uaref, gw_eventid) = ca.create_subscription(gw, mask=dbr.DBE_VALUE, callback=self.onChange)
        ioc = ca.create_channel("ioc:gwcachetest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(ioc))
        (ioc_cbref, ioc_uaref, ioc_eventid) = ca.create_subscription(ioc, mask=dbr.DBE_VALUE, callback=self.onChange)

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # limit should not have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        highVal = ioc_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 10.0, "Expected IOC warning_limit: 10; actual limit: "+ str(highVal))
        gw_ctrl = ca.get_ctrlvars(gw)
        highVal = gw_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 10.0, "Expected GW warning_limit: 10; actual limit: "+ str(highVal))

        # set warning limit on IOC
        ioc_high = ca.create_channel("ioc:gwcachetest.HIGH")
        ca.put(ioc_high, 20.0, wait=True)
        time.sleep(.1)

        # Now the limit should have been updated (if IOC supports DBE_PROPERTY)
        ioc_ctrl = ca.get_ctrlvars(ioc)
        highVal = ioc_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 20.0, "Expected IOC warning_limit: 20; actual limit: "+ str(highVal))
        if self.propSupported:
            gw_expected = 20.0
        else:
            gw_expected = 10.0
        gw_ctrl = ca.get_ctrlvars(gw)
        highVal = gw_ctrl['upper_warning_limit']
        self.assertTrue(highVal == gw_expected, "Expected GW warning_limit: {0}; actual limit: {1}".format(gw_expected, highVal))

        # set unit string on IOC
        ioc_egu = ca.create_channel("ioc:gwcachetest.EGU")
        old_egu = ca.get(ioc_egu)
        ca.put(ioc_egu, "foo", wait=True)
        time.sleep(.1)

        # Now the unit string should have been updated (if IOC supports DBE_PROPERTY)
        ioc_ctrl = ca.get_ctrlvars(ioc)
        eguVal = ioc_ctrl['units']
        self.assertTrue(eguVal == "foo", "Expected IOC units string: foo; actual units string: "+ eguVal)
        if self.propSupported:
            gw_expected = "foo"
        else:
            gw_expected = old_egu
        gw_ctrl = ca.get_ctrlvars(gw)
        eguVal = gw_ctrl['units']
        self.assertTrue(eguVal == gw_expected, "Expected GW units string: {0}; actual units string: {1}".format(gw_expected, eguVal))


    def testPropCache_ValueGetCTRLGet(self):
        '''Get PV (value) through GW - change properties (HIGH, EGU) directly - get the DBR_CTRL of the PV through GW'''
        # gateway should show no VC (client side connection) and no PV (IOC side connection)
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 0, "Expected GW PV total count: 0, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 0, "Expected GW connected PV count: 0, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # gwcachetest is an ai record with full set of alarm limits: -100 -10 10 100
        gw = ca.create_channel("gateway:gwcachetest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        ioc = ca.create_channel("ioc:gwcachetest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # limit should not have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        highVal = ioc_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 10.0, "Expected IOC warning_limit: 10; actual limit: "+ str(highVal))
        gw_ctrl = ca.get_ctrlvars(gw)
        highVal = gw_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 10.0, "Expected GW warning_limit: 10; actual limit: "+ str(highVal))

        # set warning limit on IOC
        ioc_high = ca.create_channel("ioc:gwcachetest.HIGH")
        ca.put(ioc_high, 20.0, wait=True)
        time.sleep(.1)

        # Now the limit should have been updated (if IOC supports DBE_PROPERTY)
        ioc_ctrl = ca.get_ctrlvars(ioc)
        highVal = ioc_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 20.0, "Expected IOC warning_limit: 20; actual limit: "+ str(highVal))
        if self.propSupported:
            gw_expected = 20.0
        else:
            gw_expected = 10.0
        gw_ctrl = ca.get_ctrlvars(gw)
        highVal = gw_ctrl['upper_warning_limit']
        self.assertTrue(highVal == gw_expected, "Expected GW warning_limit: {0}; actual limit: {1}".format(gw_expected, highVal))

        # set unit string on IOC
        ioc_egu = ca.create_channel("ioc:gwcachetest.EGU")
        old_egu = ca.get(ioc_egu)
        ca.put(ioc_egu, "foo", wait=True)
        time.sleep(.1)

        # Now the unit string should have been updated (if IOC supports DBE_PROPERTY)
        ioc_ctrl = ca.get_ctrlvars(ioc)
        eguVal = ioc_ctrl['units']
        self.assertTrue(eguVal == "foo", "Expected IOC units string: foo; actual units string: "+ eguVal)
        if self.propSupported:
            gw_expected = "foo"
        else:
            gw_expected = old_egu
        gw_ctrl = ca.get_ctrlvars(gw)
        eguVal = gw_ctrl['units']
        self.assertTrue(eguVal == gw_expected, "Expected GW units string: {0}; actual units string: {1}".format(gw_expected, eguVal))


    def testPropCache_ValueGetDisconnectCTRLGet(self):
        '''Get PV (value) through GW - disconnect client - change properties (HIGH, EGU) directly - get the DBR_CTRL of the PV through GW'''
        # gateway should show no VC (client side connection) and no PV (IOC side connection)
        self.updateGwStats()
        self.assertTrue(self.vctotal == 0, "Expected GW VC total count: 0, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 0, "Expected GW PV total count: 0, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 0, "Expected GW connected PV count: 0, actual: " + str(self.connected))
        self.assertTrue(self.active == 0, "Expected GW active PV count: 0, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # gwcachetest is an ai record with full set of alarm limits: -100 -10 10 100
        gw = ca.create_channel("gateway:gwcachetest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        ioc = ca.create_channel("ioc:gwcachetest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # limit should not have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        highVal = ioc_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 10.0, "Expected IOC warning_limit: 10; actual limit: "+ str(highVal))
        eguVal = ioc_ctrl['units']
        self.assertTrue(eguVal == "wobbles", "Expected IOC units string: wobbles; actual units string: "+ eguVal)
        gw_ctrl = ca.get_ctrlvars(gw)
        highVal = gw_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 10.0, "Expected GW warning_limit: 10; actual limit: "+ str(highVal))
        eguVal = gw_ctrl['units']
        self.assertTrue(eguVal == "wobbles", "Expected GW units string: wobbles; actual units string: "+ eguVal)

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

        # set warning limit on IOC
        ioc_high = ca.create_channel("ioc:gwcachetest.HIGH")
        ca.put(ioc_high, 20.0, wait=True)
        # set unit string on IOC
        ioc_egu = ca.create_channel("ioc:gwcachetest.EGU")
        ca.put(ioc_egu, "foo", wait=True)
        time.sleep(.1)

        # reconnect Gateway and IOC
        gw = ca.create_channel("gateway:gwcachetest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        ioc = ca.create_channel("ioc:gwcachetest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(gw))

        # gateway should show one VC and one connected active PV
        self.updateGwStats()
        self.assertTrue(self.vctotal == 1, "Expected GW VC total count: 1, actual: " + str(self.vctotal))
        self.assertTrue(self.pvtotal == 1, "Expected GW PV total count: 1, actual: " + str(self.pvtotal))
        self.assertTrue(self.connected == 1, "Expected GW connected PV count: 1, actual: " + str(self.connected))
        self.assertTrue(self.active == 1, "Expected GW active PV count: 1, actual: " + str(self.active))
        self.assertTrue(self.inactive == 0, "Expected GW inactive PV count: 0, actual: " + str(self.inactive))

        # now the limit should have been updated
        ioc_ctrl = ca.get_ctrlvars(ioc)
        highVal = ioc_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 20.0, "Expected IOC warning_limit: 20; actual limit: "+ str(highVal))
        eguVal = ioc_ctrl['units']
        self.assertTrue(eguVal == "foo", "Expected IOC units string: foo; actual units string: "+ eguVal)
        gw_ctrl = ca.get_ctrlvars(gw)
        highVal = gw_ctrl['upper_warning_limit']
        self.assertTrue(highVal == 20.0, "Expected GW warning_limit: 20; actual limit: "+ str(highVal))
        eguVal = gw_ctrl['units']
        self.assertTrue(eguVal == "foo", "Expected GW units string: wobbles; actual units string: "+ eguVal)


if __name__ == '__main__':
    unittest.main(verbosity=2)
