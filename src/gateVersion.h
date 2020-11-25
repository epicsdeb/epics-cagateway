/*************************************************************************\
* Copyright (c) 2002 The University of Chicago, as Operator of Argonne
* National Laboratory.
* Copyright (c) 2002 Berliner Speicherring-Gesellschaft fuer Synchrotron-
* Strahlung mbH (BESSY).
* Copyright (c) 2002 The Regents of the University of California, as
* Operator of Los Alamos National Laboratory.
* This file is distributed subject to a Software License Agreement found
* in the file LICENSE that is included with this distribution.
\*************************************************************************/
#ifndef _GATEVERSION_H_
#define _GATEVERSION_H_

/*+*********************************************************************
 *
 * File:       gateVersion.h
 * Project:    CA Proxy Gateway
 *
 * Descr.:     Gateway Version Information
 *
 * Author(s):  J. Kowalkowski, J. Anderson, K. Evans (APS)
 *             R. Lange (ITER), Gasper Jansa (cosylab),
 *             Dirk Zimoch (PSI)
 *
 *********************************************************************-*/

#define GATEWAY_VERSION       2
#define GATEWAY_REVISION      1
#define GATEWAY_MODIFICATION  2
#define GATEWAY_DEV_SNAPSHOT  ""

#define stringOf(TOKEN) #TOKEN
#define GATEWAY_VERSION_STRING "PV Gateway Version " \
    stringOf(GATEWAY_VERSION) "." stringOf(GATEWAY_REVISION) "." \
    stringOf(GATEWAY_MODIFICATION) GATEWAY_DEV_SNAPSHOT

#define GATEWAY_CREDITS_STRING  \
          "Originally developed at Argonne National Laboratory and BESSY\n\n" \
          "Authors: Jim Kowalkowski, Janet Anderson, Kenneth Evans, Jr. (APS),\n" \
          "   Ralph Lange (ITER), Gasper Jansa (cosylab), Dirk Zimoch (PSI),\n" \
          "   and Murali Shankar (SLAC)\n\n"
#endif
