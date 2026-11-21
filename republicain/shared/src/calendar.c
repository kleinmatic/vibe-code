#include "republicain/calendar.h"

static int gregorian_leap(int y)
{
    return y % 4 == 0 && (y % 100 != 0 || y % 400 == 0);
}

static long before_year(int year)
{
    long y = year - 1;
    return 365L*y + y/4 - y/100 + y/400;
}

int republican_leap(int y)
{
    /* III, VII and XI reproduce the historical year starts. The calendar
     * ended during XIV; complete it as common before switching to the
     * proposed Romme rule in XV. Its divisibility tests use the Republican
     * year, not the Gregorian year in which that year starts. */
    if (y <= 14)
        return y == 3 || y == 7 || y == 11;
    return gregorian_leap(y) && y % 4000 != 0;
}

int republicain_convert(struct civil_date d, struct republican_date *out)
{
    static const int lengths[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    int m, y, length;
    long days;
    if (d.year < 1792 || d.year > 9999 || d.month < 1 || d.month > 12)
        return 0;
    /* Sep 22 is day index 265 in leap year 1792. Anchor the count here
     * once; later New Years need not fall on the same Gregorian date. */
    days = before_year(d.year) - before_year(1792) - 265;
    for (m = 1; m <= d.month; ++m) {
        length = lengths[m-1] + (m == 2 && gregorian_leap(d.year));
        if (m < d.month) days += length;
    }
    if (d.day < 1 || d.day > length) return 0;
    days += d.day - 1;
    if (days < 0) return 0;
    for (y = 1; days >= (length = 365 + republican_leap(y)); ++y)
        days -= length;
    out->year = y;
    out->ordinal = (int)days;
    return 1;
}
