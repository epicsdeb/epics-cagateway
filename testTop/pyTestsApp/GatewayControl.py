#!/usr/bin/env python
'''Controls the CA Gateway'''
import subprocess
import atexit
import time
import os
import gwtests

class GatewayControl:
    gatewayProcess = None
    DEVNULL = None

    def startGateway(self):
        '''Starts the CA Gateway'''
        gateway_commands = [gwtests.gwExecutable]
        gateway_commands.extend(["-sip", "localhost", "-sport", str(gwtests.gwPort)])
        gateway_commands.extend(["-cip", "localhost", "-cport", str(gwtests.iocPort)])
        gateway_commands.extend(["-access", "access.txt", "-pvlist", "pvlist.txt"])
        gateway_commands.extend(["-archive", "-prefix", gwtests.gwStatsPrefix])

        if gwtests.verboseGateway:
            gateway_commands.extend(["-debug", str(gwtests.gwDebug)]);
        if gwtests.verbose:
            print "Starting the CA Gateway using\n", " ".join(gateway_commands)
        if not gwtests.verboseGateway and not gwtests.verbose:
            self.DEVNULL = open(os.devnull, 'wb')
        self.gatewayProcess = subprocess.Popen(gateway_commands, stdout=self.DEVNULL, stderr=subprocess.STDOUT)
        atexit.register(self.stop)

    def stop(self):
        '''Stops the CA Gateway'''
        if self.gatewayProcess:
            self.gatewayProcess.terminate()
            self.gatewayProcess = None
        if self.DEVNULL:
            self.DEVNULL.close()


if __name__ == "__main__":
    gwtests.setup()
    print "Running the test CA Gateway in verbose mode for {0} seconds".format(gwtests.gwRunDuration)
    gwtests.verbose = True
    gwtests.verboseGateway = True
    gatewayControl = GatewayControl()
    gatewayControl.startGateway()
    time.sleep(gwtests.gwRunDuration)
    gatewayControl.stop()
