TOP=..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

TESTSCRIPTS_HOST += gwtests.py TestDBEValue.py TestDBEAlarm.py TestDBELog.py TestDBEProp.py
TESTSCRIPTS_HOST += TestPropertyCache.py
TESTSCRIPTS_HOST += TestEnumPropCache.py
TESTSCRIPTS_HOST += TestStructures.py
TESTSCRIPTS_HOST += IOCControl.py GatewayControl.py

TESTFILES += test.db
TESTFILES += access.txt
#TESTFILES += pvlist.txt   # Done in an explicit recipe line below

CLEANS += *.pyc $(TESTFILES) pvlist.txt gateway.*

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

ifeq ($(T_A),$(EPICS_HOST_ARCH))

ifeq ($(BASE_3_14),YES)
clean::
	@$(RM) $(CLEANS)
endif

runtests:
	nosetests

tapfiles:
	nosetests --with-tap

%.py: ../%.py
	$(ECHO) "Copying test script $@"
	@$(INSTALL) -m $(INSTALL_PERMISSIONS) $< .

# Workaround for 3.14 make rules: special target to avoid circular dependencies
build runtests: testfiles
testfiles: $(TESTFILES:%=../%)
	$(ECHO) "Copying test files $(TESTFILES)"
	@$(CP) $^ .
ifeq ($(USE_PCRE),YES)
	$(ECHO) "Using pvlist.txt for PCRE"
	@$(CP) ../pvlist_pcre.txt pvlist.txt
else
	$(ECHO) "Using pvlist.txt for BRE"
	@$(CP) ../pvlist_bre.txt  pvlist.txt
endif

endif
