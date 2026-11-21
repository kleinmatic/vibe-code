/* Default adapter for targets with a standard C runtime. */
#include <time.h>
#include "republicain/platform.h"

int republicain_now(struct civil_date *out, long *seconds_since_midnight)
{
    time_t now = time(NULL);
    struct tm *local;

    if (now == (time_t)-1)
        return 0;
    local = localtime(&now);
    if (local == NULL)
        return 0;
    out->year = local->tm_year + 1900;
    out->month = local->tm_mon + 1;
    out->day = local->tm_mday;
    *seconds_since_midnight = local->tm_hour * 3600L + local->tm_min * 60L
                            + (local->tm_sec > 59 ? 59 : local->tm_sec);
    return 1;
}
