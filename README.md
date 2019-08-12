# Channel Access PV Gateway
[![Build Status](https://travis-ci.org/epics-extensions/ca-gateway.svg?branch=master)](https://travis-ci.org/epics-extensions/ca-gateway)

The [EPICS](https://epics-controls.org) Channel Access PV Gateway is both a 
Channel Access server and Channel Access client.
It provides a means for many clients to access a process variable,
while making only one connection to the server that owns the process variable.

It also provides additional access security beyond that on the server.
It thus protects critical servers while providing possibly restricted access
to needed process variables.

The Gateway typically runs on a machine with multiple network cards,
and the clients and the server may be on different subnets.

## Continuous Integration

The CI jobs for CA Gateway are provided by
[Travis](https://travis-ci.org/epics-extensions/ca-gateway).

## Links

More details are available on the
[CA Gateway main web page](http://www.aps.anl.gov/epics/extensions/gateway/).
