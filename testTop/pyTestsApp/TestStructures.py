#!/usr/bin/env python
import sys
import os
import unittest
import epics
from epics import ca, dbr
import IOCControl
import GatewayControl
import gwtests
import time
import subprocess

class TestStructures(unittest.TestCase):
    '''Testing structures going through the Gateway
    Set up a connection directly and through the Gateway - change a property - check consistency of data
    '''

    def setUp(self):
        gwtests.setup()
        self.iocControl = IOCControl.IOCControl()
        self.gatewayControl = GatewayControl.GatewayControl()
        self.iocControl.startIOC()
        self.gatewayControl.startGateway()
        self.propSupported = False
        self.eventsReceivedIOC = 0
        self.eventsReceivedGW = 0
        os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
        os.environ["EPICS_CA_ADDR_LIST"] = "localhost:{0} localhost:{1}".format(gwtests.iocPort,gwtests.gwPort)
        ca.initialize_libca()

    def tearDown(self):
        ca.finalize_libca()
        self.gatewayControl.stop()
        self.iocControl.stop()

    def onChangeIOC(self, pvname=None, **kws):
        self.eventsReceivedIOC += 1
        self.iocStruct = kws
        if gwtests.verbose:
            fmt = 'New Value for %s value=%s, kw=%s\n'
            sys.stdout.write(fmt % (pvname, str(kws['value']), repr(kws)))
            sys.stdout.flush()

    def onChangeGW(self, pvname=None, **kws):
        self.eventsReceivedGW += 1
        self.gwStruct = kws
        if gwtests.verbose:
            fmt = 'New Value for %s value=%s, kw=%s\n'
            sys.stdout.write(fmt % (pvname, str(kws['value']), repr(kws)))
            sys.stdout.flush()

    def compareStructures(self):
        are_diff = False
        diffs = []
        for k in self.iocStruct.keys():
            if k != "chid" and (self.iocStruct[k] != self.gwStruct[k]):
                are_diff = True
                diffs.append("Element '{0}' : GW has '{1}', IOC has '{2}'"
                .format(k, str(self.gwStruct[k]), str(self.iocStruct[k])))
        return are_diff, diffs

    def testCtrlStruct_ValueMonitor(self):
        '''Monitor PV (value events) through GW - change value and properties directly - check CTRL structure consistency'''
        diffs = []

        # gwcachetest is an ai record with full set of alarm limits: -100 -10 10 100
        gw = ca.create_channel("gateway:gwcachetest")
        connected = ca.connect_channel(gw, timeout=.5)
        self.assertTrue(connected, "Could not connect to gateway channel " + ca.name(gw))
        (gw_cbref, gw_uaref, gw_eventid) = ca.create_subscription(gw, mask=dbr.DBE_VALUE, use_ctrl=True, callback=self.onChangeGW)
        ioc = ca.create_channel("ioc:gwcachetest")
        connected = ca.connect_channel(ioc, timeout=.5)
        self.assertTrue(connected, "Could not connect to ioc channel " + ca.name(ioc))
        (ioc_cbref, ioc_uaref, ioc_eventid) = ca.create_subscription(ioc, mask=dbr.DBE_VALUE, use_ctrl=True, callback=self.onChangeIOC)

        # set value on IOC
        ioc_value = ca.create_channel("ioc:gwcachetest")
        ca.put(ioc_value, 10.0, wait=True)
        time.sleep(.1)

        self.assertTrue(self.eventsReceivedIOC == self.eventsReceivedGW,
        "After setting value, no. of received updates differ: GW {0}, IOC {1}"
        .format(str(self.eventsReceivedGW), str(self.eventsReceivedIOC)))
        (are_diff, diffs) = self.compareStructures()
        self.assertTrue(are_diff == False,
        "At update {0} (change value), received structure updates differ:\n\t{1}"
        .format(str(self.eventsReceivedIOC), "\n\t".join(diffs)))

        # set property on IOC
        ioc_hihi = ca.create_channel("ioc:gwcachetest.HIHI")
        ca.put(ioc_hihi, 123.0, wait=True)
        ca.put(ioc_value, 11.0, wait=True) # trigger update
        time.sleep(.1)

        self.assertTrue(self.eventsReceivedIOC == self.eventsReceivedGW,
        "After setting property, no. of received updates differ: GW {0}, IOC {1}"
        .format(str(self.eventsReceivedGW), str(self.eventsReceivedIOC)))
        (are_diff, diffs) = self.compareStructures()
        self.assertTrue(are_diff == False,
        "At update {0} (change property), received structure updates differ:\n\t{1}"
        .format(str(self.eventsReceivedIOC), "\n\t".join(diffs)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
