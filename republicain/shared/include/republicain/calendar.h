#ifndef REPUBLICAIN_CALENDAR_H
#define REPUBLICAIN_CALENDAR_H
#include "republicain/date.h"
/* Ordinal is zero-based; 360 and up are complementary days. */
struct republican_date { int year, ordinal; };
int republican_leap(int year);
int republicain_convert(struct civil_date date, struct republican_date *out);
#endif
