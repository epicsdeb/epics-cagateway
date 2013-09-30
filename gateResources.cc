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
// Author: Jim Kowalkowski
// Date: 2/96

// KE: strDup() comes from base/src/gdd/aitHelpers.h
// Not clear why strdup() is not used

#define GATE_RESOURCE_FILE 1

#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>

#ifdef WIN32
/* WIN32 does not have unistd.h and does not define the following constants */
# define F_OK 00
# define W_OK 02
# define R_OK 04
# include <direct.h>     /* for getcwd (usually in sys/parm.h or unistd.h) */
# include <io.h>         /* for access, chmod  (usually in unistd.h) */
#else
# include <unistd.h>
# include <sys/utsname.h>
#endif

#include "cadef.h"

#include "gateResources.h"
#include "gateAs.h"
#include <gddAppTable.h>
#include <dbMapper.h>

// Global variables
gateResources* global_resources;

// ---------------------------- utilities ------------------------------------


// Gets current time and puts it in a static array The calling program
// should copy it to a safe place e.g. strcpy(savetime,timestamp());
char *timeStamp(void)
{
	static char timeStampStr[16];
	long now;
	struct tm *tblock;
	
	time(&now);
	tblock=localtime(&now);
	strftime(timeStampStr,20,"%b %d %H:%M:%S",tblock);
	
	return timeStampStr;
}

// Gets current time and puts it in a static array The calling program
// should copy it to a safe place e.g. strcpy(savetime,timestamp());
char *timeString(time_t time)
{
	static char timeStr[80];
	int rem=time;
	int days=rem/86400;
	rem-=days*86400;
	int hours=rem/3600;
	rem-=hours*3600;
	int min=rem/60;
	rem-=min*60;
	int sec=rem;
	sprintf(timeStr,"%3d:%02d:%02d:%02d",days,hours,min,sec);
	return timeStr;
}

// Gets the computer name and allocates memory for it using strDup
// (from base/src/gdd/aitHelpers.h)
char *getComputerName(void)
{
	char*name=NULL;

#ifdef WIN32
	TCHAR computerName[MAX_COMPUTERNAME_LENGTH+1];
	DWORD size=MAX_COMPUTERNAME_LENGTH+1;
	// Will probably be uppercase
	BOOL status=GetComputerName(computerName,&size);
	if(status && size > 0) {
		// Convert to lowercase and copy
		// OK for ANSI.  Won't work for Unicode w/o conversion.
		char *pChar=computerName;
		while(*pChar) *pChar=tolower(*pChar++);
		name=strDup(computerName);
	}
#else
	struct utsname ubuf;
	if(uname(&ubuf) >= 0) {
		// Use the name of the host
		name=strDup(ubuf.nodename);
	}
#endif

	return name;
}

gateResources::gateResources(void)
{
	as = NULL;
    if(access(GATE_PV_ACCESS_FILE,F_OK)==0)
      access_file=strDup(GATE_PV_ACCESS_FILE);
    else
      access_file=NULL;
    
    if(access(GATE_PV_LIST_FILE,F_OK)==0)
      pvlist_file=strDup(GATE_PV_LIST_FILE);
    else
      pvlist_file=NULL;
    
    if(access(GATE_COMMAND_FILE,F_OK)==0)
      command_file=strDup(GATE_COMMAND_FILE);
    else
      command_file=NULL;
      
      
    
	// Miscellaneous initializations
	putlog_file=NULL;
	putlogFp=NULL;
	report_file=strDup(GATE_REPORT_FILE);
    debug_level=0;
    ro=0;
	serverMode=false;
#ifdef RESERVE_FOPEN_FD
	reserveFp = NULL;
#endif
    
    setEventMask(DBE_VALUE | DBE_ALARM);
    setConnectTimeout(GATE_CONNECT_TIMEOUT);
    setInactiveTimeout(GATE_INACTIVE_TIMEOUT);
    setDeadTimeout(GATE_DEAD_TIMEOUT);
    setDisconnectTimeout(GATE_DISCONNECT_TIMEOUT);
    setReconnectInhibit(GATE_RECONNECT_INHIBIT);
    
    gddApplicationTypeTable& tt = gddApplicationTypeTable::AppTable();
    
	gddMakeMapDBR(tt);
	
	appValue=tt.getApplicationType("value");
	appUnits=tt.getApplicationType("units");
	appEnum=tt.getApplicationType("enums");
	appAll=tt.getApplicationType("all");
	appFixed=tt.getApplicationType("fixed");
	appAttributes=tt.getApplicationType("attributes");
	appMenuitem=tt.getApplicationType("menuitem");
	// RL: Should this rather be included in the type table?
	appSTSAckString=gddDbrToAit[DBR_STSACK_STRING].app;
}

gateResources::~gateResources(void)
{
	if(access_file)	delete [] access_file;
	if(pvlist_file)	delete [] pvlist_file;
	if(command_file) delete [] command_file;
	if(putlog_file) delete [] putlog_file;
	if(report_file) delete [] report_file;
}

int gateResources::appValue=0;
int gateResources::appEnum=0;
int gateResources::appAll=0;
int gateResources::appMenuitem=0;
int gateResources::appFixed=0;
int gateResources::appUnits=0;
int gateResources::appAttributes=0;
int gateResources::appSTSAckString=0;

int gateResources::setListFile(const char* file)
{
	if(pvlist_file) delete [] pvlist_file;
	pvlist_file=strDup(file);
	return 0;
}

int gateResources::setAccessFile(const char* file)
{
	if(access_file) delete [] access_file;
	access_file=strDup(file);
	return 0;
}

int gateResources::setCommandFile(const char* file)
{
	if(command_file) delete [] command_file;
	command_file=strDup(file);
	return 0;
}

int gateResources::setPutlogFile(const char* file)
{
	if(putlog_file) delete [] putlog_file;
	putlog_file=strDup(file);
	return 0;
}

int gateResources::setReportFile(const char* file)
{
	if(report_file) delete [] report_file;
	report_file=strDup(file);
	return 0;
}

int gateResources::setDebugLevel(int level)
{
	debug_level=level;
	return 0;
}

int gateResources::setUpAccessSecurity(void)
{
	as=new gateAs(pvlist_file,access_file);
	return 0;
}

#ifdef RESERVE_FOPEN_FD
// Functions to try to reserve a file descriptor to use for fopen.  On
// Solaris, at least, fopen is limited to FDs < 256.  These could all
// be used by CA and CAS sockets if there are connections to enough
// IOCs  These functions try to reserve a FD < 256.
FILE *gateResources::fopen(const char *filename, const char *mode)
{
	// Close the dummy file holding the FD open
    if(reserveFp) ::fclose(reserveFp);
    reserveFp=NULL;
	
	// Open the file.  It should use the lowest available FD, that is,
	// the one we just made available.
    FILE *fp=::fopen(filename,mode);
    if(!fp) {
		// Try to get the reserved one back
		reserveFp=::fopen(GATE_RESERVE_FILE,"w");
    }
	
    return fp;
}

int gateResources::fclose(FILE *stream)
{
	// Close the file
    int ret=::fclose(stream);
	
	// Open the dummy file to reserve the FD just made available
    reserveFp=::fopen(GATE_RESERVE_FILE,"w");
	
    return ret;
}

FILE *gateResources::openReserveFile(void)
{
    reserveFp=::fopen(GATE_RESERVE_FILE,"w");
    return reserveFp;
}
#endif

gateAs* gateResources::getAs(void)
{
	if(as==NULL) setUpAccessSecurity();
	return as;
}

/* **************************** Emacs Editing Sequences ***************** */
/* Local Variables: */
/* tab-width: 4 */
/* c-basic-offset: 4 */
/* c-comment-only-line-offset: 0 */
/* c-file-offsets: ((substatement-open . 0) (label . 0)) */
/* End: */
