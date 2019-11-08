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
#ifndef _GATESERVER_H_
#define _GATESERVER_H_

// Define this to manage file descriptors
//#define USE_FDS

/*+*********************************************************************
 *
 * File:       gateServer.h
 * Project:    CA Proxy Gateway
 *
 * Descr.:     Server class header
 *             - CAS virtual interface
 *             - Gateway lists and hashes
 *             - Server statistics variables
 *
 * Author(s):  J. Kowalkowski, J. Anderson, K. Evans (APS)
 *             R. Lange (BESSY)
 *
 *********************************************************************-*/

#include <sys/types.h>

#ifdef _WIN32
#else
# include <unistd.h>
# include <sys/time.h>
#endif

#include "casdef.h"
#include "tsHash.h"
#include "fdManager.h"

#include "gateResources.h"
#include "gateVc.h"
#include "gatePv.h"
#include "gateStat.h"

class gateServer;
class gateAs;
class gateStat;
class gdd;

typedef struct exception_handler_args EXCEPT_ARGS;

// ---------------------- list nodes ------------------------

class gatePvNode : public tsDLHashNode<gatePvNode>
{
private:
	gatePvNode(void);
	gatePvData* pvd;

public:
	gatePvNode(gatePvData& d) : pvd(&d) { }
	~gatePvNode(void) { }

	gatePvData* getData(void) { return pvd; }
	void destroy(void) { delete pvd; delete this; }
};

#ifdef USE_FDS
// ---------------------- fd manager ------------------------

class gateFd : public fdReg
{
public:
	gateFd(const int fdIn,const fdRegType typ,gateServer& s);
	virtual ~gateFd(void);
private:
	virtual void callBack(void);
	gateServer& server;

#if DEBUG_TIMES
	static int count;
#endif

};
#endif

// ---------------------- stats -----------------------------

// server stats definitions
#ifdef STAT_PVS
# define statVcTotal      0
# define statPvTotal      1
// This should be connected, but left for backward compatibility
# define statAlive        2
# define statActive       3
# define statInactive     4
# define statUnconnected  5
# define statDead         6
# define statConnecting   7
# define statDisconnected 8
# ifdef USE_FDS
#  define statFd          9
#  define NEXT_STAT_PV   10
# else
#  define NEXT_STAT_PV    9
# endif
#else
# define NEXT_STAT_PV     0
#endif


#ifdef RATE_STATS
# define statClientEventRate NEXT_STAT_PV
# define statPostEventRate   NEXT_STAT_PV+1
# define statExistTestRate   NEXT_STAT_PV+2
# define statLoopRate        NEXT_STAT_PV+3
# define statCPUFract        NEXT_STAT_PV+4
# define statLoad            NEXT_STAT_PV+5
# define NEXT_RATE_STAT      NEXT_STAT_PV+6
#else
# define NEXT_RATE_STAT      NEXT_STAT_PV
#endif

#ifdef CAS_DIAGNOSTICS
# define statServerEventRate        NEXT_RATE_STAT
# define statServerEventRequestRate NEXT_RATE_STAT+1
# define NEXT_CONTROL_PV            NEXT_RATE_STAT+2
#else
# define NEXT_CONTROL_PV            NEXT_RATE_STAT
#endif

#ifdef CONTROL_PVS
# define statCommandFlag            NEXT_CONTROL_PV
# define statReport1Flag            NEXT_CONTROL_PV+1
# define statReport2Flag            NEXT_CONTROL_PV+2
# define statReport3Flag            NEXT_CONTROL_PV+3
# define statNewAsFlag              NEXT_CONTROL_PV+4
# define statQuitFlag               NEXT_CONTROL_PV+5
# define statQuitServerFlag         NEXT_CONTROL_PV+6
# define NEXT_HEARTBEAT_PV          NEXT_CONTROL_PV+7
#else
# define NEXT_HEARTBEAT_PV          NEXT_CONTROL_PV
#endif

#ifdef HEARTBEAT_PV
# define heartbeat                  NEXT_HEARTBEAT_PV
# define NEXT_CAS_STAT              NEXT_HEARTBEAT_PV+1
#else
# define NEXT_CAS_STAT              NEXT_HEARTBEAT_PV
#endif

// Number of server stats definitions
#define statCount NEXT_CAS_STAT

typedef struct gateServerStats
{
	const char *name;
	char *pvName;
	char *descPvName;
	gateStat *pv;
	gateStatDesc *descPv;
	// Volatile so it can be used with flags, which are volatile
	// Pointer so it will use the current value at initialization
	volatile unsigned long* init_value;
	const char *desc;
	const char *units;
	short precision;
} gateServerStats;

#if defined(RATE_STATS) || defined(CAS_DIAGNOSTICS)
#include "epicsTimer.h"
class gateRateStatsTimer : public epicsTimerNotify
{
  public:
    gateRateStatsTimer(epicsTimerQueue &queue,
      double intervalIn, gateServer *m) :
      interval(intervalIn), startTime(epicsTime::getCurrent()),
      mrg(m), timer(queue.createTimer()) {}
    virtual expireStatus expire(const epicsTime &curTime);
    void start() { timer.start(*this,interval); }
    void stop() { timer.cancel(); }
  protected:
    virtual ~gateRateStatsTimer() { timer.destroy(); }
  private:
    double interval;
    epicsTime startTime;
    gateServer *mrg;
    epicsTimer &timer;
};
#endif

// ---------------------- server ----------------------------

class gateServer : public caServer
{
public:
	gateServer(char *prefix=NULL);
	virtual ~gateServer(void);

	// caServer virtual overloads
#ifdef USE_DENYFROM
	virtual pvExistReturn pvExistTest(const casCtx& ctx, const caNetAddr& netAddr,
	  const char* pvname);
#else
	virtual pvExistReturn pvExistTest(const casCtx& ctx, const caNetAddr& netAddr,
	  const char* pvname);
	virtual pvExistReturn pvExistTest(const casCtx& ctx, const char* pvname);
#endif
	virtual pvAttachReturn pvAttach(const casCtx& ctx, const char* pvname);

	// caServer overwrite
    void generateBeaconAnomaly();

	void mainLoop(void);
	void gateCommands(const char* cfile);
	void newAs(void);
	void report1(void);
	void report2(void);
	void report3(void);
	gateAs* getAs(void) { return as; }
	casEventMask select_mask;
	casEventMask alh_mask;

	time_t start_time;
	unsigned long exist_count;
#if statCount
	gateServerStats *getStatTable(int type) { return &stat_table[type]; }
	void setStat(int type, double val);
	void setStat(int type, unsigned long val);
	caStatus processStat(int type, double val);
	void clearStat(int type, gateStatType statType);
	void initStats(char *prefix);
	char* stat_prefix;
    size_t stat_prefix_len;
	gateServerStats stat_table[statCount];
#endif
#ifdef STAT_PVS
	unsigned long total_vc;
	unsigned long total_pv;
	unsigned long total_alive;
	unsigned long total_active;
	unsigned long total_inactive;
	unsigned long total_unconnected;
	unsigned long total_dead;
	unsigned long total_connecting;
	unsigned long total_disconnected;
# ifdef USE_FDS
	unsigned long total_fd;
# endif
#endif
#ifdef RATE_STATS
	unsigned long client_event_count;
	unsigned long post_event_count;
	unsigned long loop_count;
#endif

	// CAS application management functions
	void checkEvent(void);

	static void quickDelay(void);
	static void normalDelay(void);
	static double currentDelay(void);

	int pvAdd(const char* name, gatePvData& pv);
	int pvDelete(const char* name, gatePvData*& pv);
	int pvFind(const char* name, gatePvData*& pv);
	int pvFind(const char* name, gatePvNode*& pv);

	int conAdd(const char* name, gatePvData& pv);
	int conDelete(const char* name, gatePvData*& pv);
	int conFind(const char* name, gatePvData*& pv);
	int conFind(const char* name, gatePvNode*& pv);

	int vcAdd(const char* name, gateVcData& pv);
	int vcDelete(const char* name, gateVcData*& pv);
	int vcFind(const char* name, gateVcData*& pv);

	void connectCleanup(void);
	void inactiveDeadCleanup(void);

	void setFirstReconnectTime(void);
	void markRefreshSuppressed(void);
	void markNoRefreshSuppressed(void);

	time_t timeDeadCheck(void) const;
	time_t timeInactiveCheck(void) const;
	time_t timeConnectCleanup(void) const;
	time_t timeSinceLastBeacon(void) const;

	tsDLHashList<gateVcData>* vcList(void) { return &vc_list; }
	tsDLHashList<gatePvNode>* pvList(void) { return &pv_list; }
	tsDLHashList<gatePvNode>* pvConList(void) { return &pv_con_list; }

	void setQuitFlag(unsigned long flag) { quit_flag=flag; }

private:
	tsDLHashList<gatePvNode> pv_list;		// client pv list
	tsDLHashList<gatePvNode> pv_con_list;	// pending client pv connection list
	tsDLHashList<gateVcData> vc_list;		// server pv list

	void setDeadCheckTime(void);
	void setInactiveCheckTime(void);
	void setConnectCheckTime(void);

	int refreshSuppressed(void) const;

	time_t last_dead_cleanup;		// checked dead PVs for cleanup here
	time_t last_inactive_cleanup;	// checked inactive PVs for cleanup here
	time_t last_connect_cleanup;	// cleared out connect pending list here
	time_t last_beacon_time;	    // last time a beacon was sent

	int suppressed_refresh_flag;	// flag to remember suppressed beacons

	gateAs* as;

	static double delay_quick;
	static double delay_normal;
	static double delay_current;

	static volatile unsigned long command_flag;
	static volatile unsigned long report1_flag;
	static volatile unsigned long report2_flag;
	static volatile unsigned long report3_flag;
	static volatile unsigned long newAs_flag;
	static volatile unsigned long quit_flag;
	static volatile unsigned long quitserver_flag;

public:
#ifndef _WIN32
	static void sig_usr1(int);
	static void sig_usr2(int);
#endif
#ifdef USE_FDS
	static void fdCB(void* ua, int fd, int opened);
#endif
	static void exCB(EXCEPT_ARGS args);
	static void errlogCB(void *userData, const char *message);
};

// --------- time functions
inline time_t gateServer::timeDeadCheck(void) const
	{ return time(NULL)-last_dead_cleanup; }
inline time_t gateServer::timeInactiveCheck(void) const
	{ return time(NULL)-last_inactive_cleanup; }
inline time_t gateServer::timeConnectCleanup(void) const
	{ return time(NULL)-last_connect_cleanup; }
inline time_t gateServer::timeSinceLastBeacon(void) const
	{ return time(NULL)-last_beacon_time; }

inline void gateServer::setDeadCheckTime(void)
    { time(&last_dead_cleanup); }
inline void gateServer::setInactiveCheckTime(void)
	{ time(&last_inactive_cleanup); }
inline void gateServer::setConnectCheckTime(void)
	{ time(&last_connect_cleanup); }
inline void gateServer::setFirstReconnectTime(void)
	{ time(&last_beacon_time); }

inline void gateServer::markRefreshSuppressed(void)
	{ suppressed_refresh_flag = 1; }
inline void gateServer::markNoRefreshSuppressed(void)
	{ suppressed_refresh_flag = 0; }
inline int gateServer::refreshSuppressed(void) const
    { return (suppressed_refresh_flag)?1:0; }

// --------- add functions
inline int gateServer::pvAdd(const char* name, gatePvData& pv)
{
	gatePvNode* x = new gatePvNode(pv);
	return pv_list.add(name,*x);
}
inline int gateServer::conAdd(const char* name, gatePvData& pv)
{
	gatePvNode* x = new gatePvNode(pv);
	return pv_con_list.add(name,*x);
}

// --------- find functions
inline int gateServer::pvFind(const char* name, gatePvNode*& pv)
	{ return pv_list.find(name,pv); }
inline int gateServer::conFind(const char* name, gatePvNode*& pv)
	{ return pv_con_list.find(name,pv); }

inline int gateServer::pvFind(const char* name, gatePvData*& pv)
{
	gatePvNode* n;
	int rc;
	if((rc=pvFind(name,n))==0) pv=n->getData(); else pv=NULL;
	return rc;
}

inline int gateServer::conFind(const char* name, gatePvData*& pv)
{
	gatePvNode* n;
	int rc;
	if((rc=conFind(name,n))==0) pv=n->getData(); else pv=NULL;
	return rc;
}

// --------- delete functions
inline int gateServer::pvDelete(const char* name, gatePvData*& pv)
{
	gatePvNode* n;
	int rc;
    if ((rc = pvFind(name,n)) == 0) {
        pv_list.remove(name, n);
        pv = n->getData();
        delete n;
    }
    else
        pv = NULL;
    return rc;
}
inline int gateServer::conDelete(const char* name, gatePvData*& pv)
{
	gatePvNode* n;
	int rc;
    if ((rc = conFind(name,n)) == 0) {
        pv_con_list.remove(name, n);
        pv = n->getData();
        delete n;
    }
    else
        pv = NULL;
    return rc;
}

inline int gateServer::vcAdd(const char* name, gateVcData& pv)
	{ return vc_list.add(name,pv); }
inline int gateServer::vcFind(const char* name, gateVcData*& pv)
	{ return vc_list.find(name,pv); }
inline int gateServer::vcDelete(const char* name, gateVcData*& vc)
	{ return vc_list.remove(name,vc); }

#endif

/* **************************** Emacs Editing Sequences ***************** */
/* Local Variables: */
/* tab-width: 4 */
/* c-basic-offset: 4 */
/* c-comment-only-line-offset: 0 */
/* c-file-offsets: ((substatement-open . 0) (label . 0)) */
/* End: */
