TOP=..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

# Test programs
PYTESTS += TestDBEAlarm.py
PYTESTS += TestDBELog.py
PYTESTS += TestDBEProp.py
PYTESTS += TestDBEValue.py
PYTESTS += TestEnumPropertyCache.py
PYTESTS += TestPropertyCache.py
PYTESTS += TestStructures.py
PYTESTS += TestWaveformWithCAMaxArrayBytes.py

TAPFILES = $(PYTESTS:.py=.tap)

TESTFILES += test.db
TESTFILES += access.txt

# Which pvlist.txt file depends on USE_PCRE
USE_PCRE ?= NO
PVLIST_YES = pvlist_pcre.txt
PVLIST_NO = pvlist_bre.txt

CLEANS += *.pyc $(TESTFILES) pvlist.txt gateway.* *.tap

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

ifeq ($(T_A),$(EPICS_HOST_ARCH))

# Environment required by some test programs
export BASE ?= $(EPICS_VERSION).$(EPICS_REVISION)
export EPICS_BASE

ifeq ($(BASE_3_14),YES)
clean::
	@$(RM) $(CLEANS)
endif

runtests:
	nosetests $(PYTESTS:%=../%)

$(TAPFILES): Test%.tap: ../Test%.py
	nosetests --with-tap $<

# Workaround for 3.14 make rules: special target to avoid circular dependencies
build runtests tapfiles: testfiles pvlist.txt
testfiles: $(TESTFILES:%=../%)
	$(ECHO) "Copying test files $(TESTFILES)"
	@$(CP) $^ .

pvlist.txt: ../$(PVLIST_$(USE_PCRE))
	$(ECHO) "Copying $< to $@ (USE_PCRE: $(USE_PCRE))"
	@$(CP) $< $@

endif
