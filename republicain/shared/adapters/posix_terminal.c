#include <langinfo.h>
#include <locale.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include "republicain/terminal.h"

struct terminal republicain_terminal(void)
{
    struct terminal t = {0, 0, 0};
    const char *term = getenv("TERM");
#ifdef TIOCGWINSZ
    struct winsize ws;
    if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0)
        t.columns = ws.ws_col;
#endif
    if (isatty(STDOUT_FILENO) && term && *term && strcmp(term, "dumb")) {
        t.bold = 1;
        if (setlocale(LC_CTYPE, "")) {
            const char *cs = nl_langinfo(CODESET);
            t.utf8 = !strcmp(cs, "UTF-8") || !strcmp(cs, "UTF8");
        }
    }
    return t;
}
