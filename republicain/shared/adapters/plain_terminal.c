#include "republicain/terminal.h"
/* For targets without a verified terminal API. Zero columns means "unknown":
 * the caller still wraps using COLUMNS or 80, even without tty detection. */
struct terminal republicain_terminal(void)
{
    struct terminal t = {0, 0, 0};
    return t;
}
