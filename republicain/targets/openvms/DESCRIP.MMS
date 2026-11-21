! Invoke MMS from [.targets.openvms].
CFLAGS = /INCLUDE_DIRECTORY=([--.shared.include])
OBJS = main.obj,calendar.obj,names.obj,iso_c_clock.obj,plain_terminal.obj

republicain.exe : $(OBJS)
	LINK/EXECUTABLE=republicain.exe $(OBJS)

main.obj : [--.shared.src]main.c [--.shared.include.republicain]calendar.h -
 [--.shared.include.republicain]date.h [--.shared.include.republicain]names.h -
 [--.shared.include.republicain]platform.h [--.shared.include.republicain]terminal.h
	CC $(CFLAGS)/OBJECT=main.obj [--.shared.src]main.c
calendar.obj : [--.shared.src]calendar.c [--.shared.include.republicain]calendar.h -
 [--.shared.include.republicain]date.h
	CC $(CFLAGS)/OBJECT=calendar.obj [--.shared.src]calendar.c
names.obj : [--.shared.src]names.c [--.shared.src]rural_en.inc [--.shared.include.republicain]names.h
	CC $(CFLAGS)/OBJECT=names.obj [--.shared.src]names.c
iso_c_clock.obj : [--.shared.adapters]iso_c_clock.c [--.shared.include.republicain]platform.h -
 [--.shared.include.republicain]date.h
	CC $(CFLAGS)/OBJECT=iso_c_clock.obj [--.shared.adapters]iso_c_clock.c
plain_terminal.obj : [--.shared.adapters]plain_terminal.c [--.shared.include.republicain]terminal.h
	CC $(CFLAGS)/OBJECT=plain_terminal.obj [--.shared.adapters]plain_terminal.c
