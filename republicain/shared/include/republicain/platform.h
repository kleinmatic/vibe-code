#ifndef REPUBLICAIN_PLATFORM_H
#define REPUBLICAIN_PLATFORM_H

#include "republicain/date.h"

/* Return 1 on success, 0 if the platform clock cannot supply a date. */
int republicain_now(struct civil_date *out, long *seconds_since_midnight);

#endif
