TARGET ?= linux
# Select by destination OS, not by the compiler host. Two targets can select
# the same adapter today and still need different native headers or link flags
# later. Keep those differences in the target profile, out of shared/src.
include targets/$(TARGET)/build.mk

INCLUDES = -Ishared/include
CORE = shared/src/calendar.c shared/src/names.c
SOURCES = shared/src/main.c $(CORE) shared/adapters/iso_c_clock.c $(TERMINAL)
HEADERS = $(wildcard shared/include/republicain/*.h) shared/src/rural_en.inc
OUT = build/$(TARGET)

all: $(OUT)/republicain

$(OUT)/republicain: $(SOURCES) $(HEADERS) targets/$(TARGET)/build.mk Makefile
	mkdir -p $(OUT)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(INCLUDES) $(SOURCES) $(LDFLAGS) $(LDLIBS) -o $@

test-special: all
	python3 tests/special_days.py $(OUT)/republicain

test: all
	python3 tests/special_days.py $(OUT)/republicain > /dev/null
	python3 tests/check.py $(OUT)/republicain

test-boundaries: all
	python3 tests/year_boundaries.py $(OUT)/republicain

.PHONY: all test test-special test-boundaries
