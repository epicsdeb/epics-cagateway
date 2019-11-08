<a target="_blank" href="http://semver.org">![Version][badge.version]</a>
<a target="_blank" href="https://travis-ci.org/epics-extensions/ca-gateway">![Travis status][badge.travis]</a>

# Channel Access PV Gateway

The [EPICS](https://epics-controls.org) Channel Access PV Gateway is both a 
Channel Access server and Channel Access client.
It provides a means for many clients to access a process variable,
while making only one connection to the server that owns the process variable.

It also provides additional access security beyond that on the server.
It thus protects critical servers while providing possibly restricted access
to needed process variables.

The Gateway typically runs on a machine with multiple network cards,
and the clients and the server may be on different subnets.

## Dependencies

The CA Gateway is using the PCAS server library and needs the PCAS module
(https://github.com/epics-modules/pcas) when compiled against EPICS 7 (>= 3.16).

If you compile the CA Gateway with caPutLog support
(https://github.com/epics-modules/caPutLog), a caPutLog version >= 3.5 is required.

## Continuous Integration

The CI jobs for CA Gateway are provided by
[Travis](https://travis-ci.org/epics-extensions/ca-gateway).

## Links

More details are available on the
[CA Gateway main web page](http://www.aps.anl.gov/epics/extensions/gateway/).

<!-- Links -->
[badge.version]: https://badge.fury.io/gh/epics-extensions%2Fca-gateway.svg
[badge.travis]: https://travis-ci.org/epics-extensions/ca-gateway.svg?branch=master
