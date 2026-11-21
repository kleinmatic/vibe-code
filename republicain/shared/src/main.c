#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "republicain/calendar.h"
#include "republicain/names.h"
#include "republicain/platform.h"
#include "republicain/terminal.h"

static int parse(const char *s, struct civil_date *d)
{
    int i;
    if (strlen(s) != 10) return 0;
    for (i = 0; i < 10; ++i) {
        if (i == 4 || i == 7) { if (s[i] != '-') return 0; }
        else if (s[i] < '0' || s[i] > '9') return 0;
    }
    d->year = atoi(s); d->month = atoi(s+5); d->day = atoi(s+8);
    return 1;
}

/* A four-digit civil year needs fewer than 32 Roman characters. */
static void format_year(char *out, int y, int arabic)
{
    static const int values[] = {1000,900,500,400,100,90,50,40,10,9,5,4,1};
    static const char *const symbols[] =
        {"M","CM","D","CD","C","XC","L","XL","X","IX","V","IV","I"};
    int i;
    if (arabic) { sprintf(out, "%d", y); return; }
    *out = '\0';
    for (i = 0; y; ++i)
        while (y >= values[i]) { strcat(out, symbols[i]); y -= values[i]; }
}

static const char *text(struct name n, int utf8)
{
    return utf8 && n.utf8 ? n.utf8 : n.plain;
}

/* Our labels use only ASCII and precomposed, single-cell French characters. */
static int cells(const char *s)
{
    int width = 0;
    for (; *s; ++s)
        if (((unsigned char)*s & 0xc0) != 0x80) ++width;
    return width;
}

/* Print one word-wrapped fragment, returning the unconsumed suffix. */
static const char *fragment(const char *s, int width, int pad)
{
    const char *p = s, *space = NULL;
    int count = 0, before_space = 0;
    while (*p && count < width) {
        if (*p == ' ') { space = p; before_space = count; }
        do { ++p; } while (((unsigned char)*p & 0xc0) == 0x80);
        ++count;
    }
    if (*p && *p != ' ' && space) { p = space; count = before_space; }
    fwrite(s, 1, (size_t)(p-s), stdout);
    if (pad) while (count++ < width) putchar(' ');
    while (*p == ' ') ++p;
    return p;
}

static void wrapped(const char *s, int width, const char *inset)
{
    do { fputs(inset, stdout); s = fragment(s, width, 0); putchar('\n'); } while (*s);
}

static void row(const char *a, const char *b, const char *c, const int widths[3], const char *inset)
{
    const char *v[3];
    int i;
    v[0] = a; v[1] = b; v[2] = c;
    do {
        fputs(inset, stdout);
        for (i = 0; i < 3; ++i) {
            fputs("| ", stdout);
            v[i] = fragment(v[i], widths[i], 1);
            putchar(' ');
        }
        puts("|");
    } while (*v[0] || *v[1] || *v[2]);
}

static void border(const int widths[3], const char *inset)
{
    int i, j;
    fputs(inset, stdout);
    for (i = 0; i < 3; ++i) {
        putchar('+');
        for (j = 0; j < widths[i] + 2; ++j) putchar('-');
    }
    puts("+");
}

static void spanning(const char *s, int width, const char *inset)
{
    do {
        fputs(inset, stdout); fputs("| ", stdout);
        s = fragment(s, width - 4, 1);
        puts(" |");
    } while (*s);
}

static const char *new_year_note(struct republican_date r, int en, int utf8)
{
    /* Explain the modern convention on the date it affects most directly,
     * 1 Vendemiaire, and only in years calculated under that convention. */
    if (r.ordinal != 0 || r.year < 15) return NULL;
    if (en) return "New Year's Day under the Romme rule, based on leap years rather than the Paris equinox.";
    return utf8 ? "Nouvel an selon la r\303\250gle de Romme, fond\303\251e sur les ann\303\251es bissextiles plut\303\264t que sur l'\303\251quinoxe de Paris." :
                  "Nouvel an selon la regle de Romme, fondee sur les annees bissextiles plutot que sur l'equinoxe de Paris.";
}

static void measure(const char *s, int *width, int *floor)
{
    int word = 0;
    if (!s) return;
    if (cells(s) > *width) *width = cells(s);
    for (; *s; ++s) {
        if (*s == ' ') word = 0;
        else if (((unsigned char)*s & 0xc0) != 0x80) ++word;
        if (word > *floor) *floor = word;
    }
}

static void render_table(const char *title, const char *heading, const char *h,
                         const char *almanac, const char *date, const char *week,
                         const char *item, const char *time_label, const char *greeting,
                         const char *note, struct terminal t, const char *inset);

static void table(struct republican_date r, const char *month, const char *year, int en, struct terminal t,
                  const char *inset, const char *time_label, const char *greeting)
{
    char date[96], week[80];
    int n = r.ordinal;
    const char *title = en ? "Today in the French Republican Calendar" :
        t.utf8 ? "Aujourd'hui dans le calendrier r\303\251publicain fran\303\247ais" :
                 "Aujourd'hui dans le calendrier republicain francais";
    const char *h = t.utf8 ? "D\303\251cade" : "Decade";
    const char *almanac = en ? "Rural Almanac" : "Almanach rural";
    const char *item;
    const char *heading = *time_label ? (en ? "Date and Time" : "Date et heure") : "Date";
    if (n < 360) {
        int w = n % 10;
        sprintf(date, "%d %s, %s %s", n%30+1, month, en ? "Year" : "an", year);
        sprintf(week, en ? "%s, day %d of 10" : "%s, jour %d sur 10",
                text(weekdays[w], t.utf8), w+1);
        week[0] += 'A' - 'a';
        if (w == 9) {
            static const char *const ord[] = {"first", "second", "third"};
            int k = n % 30 / 10;
            if (en) sprintf(week + strlen(week), " (rest day of the %s ten-day week)", ord[k]);
            else sprintf(week + strlen(week), " (repos de la %d%s %s)", k+1,
                         k == 0 ? "re" : "e", t.utf8 ? "d\303\251cade" : "decade");
        }
        item = en ? rural_en[n] : text(rural[n], t.utf8);
    } else {
        sprintf(date, en ? "Sansculottides, day %d of %d, Year %s" :
                           "Sansculottides, jour %d sur %d, an %s",
                n-359, 5 + republican_leap(r.year), year);
        strcpy(week, en ? "Outside the ten-day week" :
               t.utf8 ? "Hors de la d\303\251cade" : "Hors de la decade");
        almanac = en ? "Festival" : t.utf8 ? "F\303\252te" : "Fete";
        item = text(festivals[n-360], t.utf8);
    }
    render_table(title, heading, h, almanac, date, week, item, time_label, greeting,
                 new_year_note(r, en, t.utf8), t, inset);
}

static void render_table(const char *title, const char *heading, const char *h,
                         const char *almanac, const char *date, const char *week,
                         const char *item, const char *time_label, const char *greeting,
                         const char *note, struct terminal t, const char *inset)
{
    int widths[3] = {0,0,0}, floors[3] = {1,1,1}, width, i;
    measure(heading, &widths[0], &floors[0]);
    measure(date, &widths[0], &floors[0]);
    measure(time_label, &widths[0], &floors[0]);
    measure(greeting, &widths[0], &floors[0]);
    measure(h, &widths[1], &floors[1]);
    measure(week, &widths[1], &floors[1]);
    measure(almanac, &widths[2], &floors[2]);
    measure(item, &widths[2], &floors[2]);
    if (t.columns < 13) {
        wrapped(title, t.columns, inset);
        wrapped(heading, t.columns, inset); wrapped(date, t.columns, inset);
        if (*time_label) wrapped(time_label, t.columns, inset);
        if (greeting) wrapped(greeting, t.columns, inset);
        wrapped(h, t.columns, inset); wrapped(week, t.columns, inset);
        wrapped(almanac, t.columns, inset); wrapped(item, t.columns, inset);
        if (note) wrapped(note, t.columns, inset);
        return;
    }
    while (widths[0] + widths[1] + widths[2] + 10 > t.columns) {
        /* Four borders and six padding cells are fixed. Preserve whole
         * words until those word widths themselves exceed the budget. */
        int k = -1;
        for (i = 0; i < 3; ++i)
            if (widths[i] > floors[i] && (k < 0 || widths[i] > widths[k])) k = i;
        if (k < 0) floors[0] = floors[1] = floors[2] = 1;
        else --widths[k];
    }
    width = widths[0] + widths[1] + widths[2] + 10;
    fputs(inset, stdout); putchar('+');
    for (i = 0; i < width-2; ++i) putchar('-');
    puts("+");
    spanning(title, width, inset);
    border(widths, inset);
    if (t.bold) fputs("\033[1m", stdout);
    row(heading, h, almanac, widths, inset);
    if (t.bold) fputs("\033[0m", stdout);
    border(widths, inset);
    row(date, week, item, widths, inset);
    if (*time_label) row(time_label, "", "", widths, inset);
    if (greeting) row(greeting, "", "", widths, inset);
    border(widths, inset);
    if (note) {
        spanning(note, width, inset);
        border(widths, inset);
    }
}

static void json_string(const char *s)
{
    if (!s) { fputs("null", stdout); return; }
    putchar('"');
    while (*s) {
        unsigned char c = (unsigned char)*s++;
        if (c == '"' || c == '\\') putchar('\\');
        if (c < 32) printf("\\u%04x", (unsigned)c);
        else putchar(c);
    }
    putchar('"');
}

static void json_date(struct civil_date d, struct republican_date r, int en,
                      const char *year, int gloss, const char *clock, const char *greeting)
{
    int n = r.ordinal, regular = n < 360, m = n / 30;
    printf("{\"gregorian_date\":\"%04d-%02d-%02d\",\"year\":%d,\"year_label\":",
           d.year, d.month, d.day, r.year);
    json_string(year);
    fputs(",\"month\":", stdout); json_string(regular ? text(months[m], 1) : NULL);
    fputs(",\"month_meaning\":", stdout);
    json_string(regular && gloss ? (en ? month_gloss_en[m] : text(month_gloss_fr[m], 1)) : NULL);
    if (regular)
        printf(",\"day\":%d,\"decade\":%d,\"day_of_decade\":%d,\"complementary_day\":null",
               n%30+1, n%30/10+1, n%10+1);
    else
        printf(",\"day\":null,\"decade\":null,\"day_of_decade\":null,\"complementary_day\":%d", n-359);
    fputs(",\"weekday\":", stdout); json_string(regular ? text(weekdays[n%10], 1) : NULL);
    fputs(",\"rural_almanac\":", stdout);
    json_string(regular ? (en ? rural_en[n] : text(rural[n], 1)) : NULL);
    fputs(",\"festival\":", stdout); json_string(regular ? NULL : text(festivals[n-360], 1));
    fputs(",\"decimal_time\":", stdout); json_string(clock);
    fputs(",\"greeting\":", stdout); json_string(greeting);
    fputs(",\"note\":", stdout); json_string(new_year_note(r, en, 1));
    puts("}");
}

static void dedication(int n, int english, int utf8)
{
    int w = n % 10;
    const char *weekday;
    if (n >= 360) {
        fputs(english ? "Outside the ten-day week, the calendar celebrates " :
              utf8 ? "Hors de la d\303\251cade, on c\303\251l\303\250bre la " :
                     "Hors de la decade, on celebre la ", stdout);
        fputs(text(festivals[n-360], utf8), stdout);
    } else {
        weekday = text(weekdays[w], utf8);
        /* All ten names start with a lowercase ASCII letter. */
        putchar(weekday[0] - 'a' + 'A');
        fputs(weekday+1, stdout);
        if (english) {
            if (w == 0) fputs(" opens the ten-day week with a dedication: ", stdout);
            else if (w == 9) fputs(", the rest day, closes the ten-day week by honouring a tool: ", stdout);
            else if (w == 4) fputs(", day 5 of the ten-day week, honours an animal: ", stdout);
            else printf(", day %d of the ten-day week, has a rural dedication: ", w+1);
            fputs(rural_en[n], stdout);
        } else {
            const char *decade = utf8 ? "d\303\251cade" : "decade";
            if (w == 0) printf(" ouvre la %s ; ", decade);
            else if (w == 9) printf(", jour de repos, termine la %s ; ", decade);
            else printf(", jour %d de la %s ; ", w+1, decade);
            if (w == 9) fputs("outil ", stdout);
            if (w == 4) fputs("animal ", stdout);
            fputs(utf8 ? "\303\240 l'honneur : " : "a l'honneur : ", stdout);
            fputs(text(rural[n], utf8), stdout);
        }
    }
    putchar('.');
}

int main(int argc, char **argv)
{
    static const char usage[] = "Usage: republicain [--help] [--lang=fr|en] [--numerals=roman|arabic]"
                  " [--format=table|line|json] [--[no-]month-gloss] [--style=auto|plain]"
                  " [--[no-]decimal-time] [YYYY-MM-DD]\n";
    struct civil_date d;
    struct republican_date r;
    struct terminal t;
    const char *arg = NULL;
    const char *inset = "";
    const char *greeting;
    char year[32], month[48] = "", time_label[64] = "";
    int clock = -1, gloss = 1, auto_style = 1;
    long seconds = 0;
    enum { TABLE, LINE, JSON } format = TABLE;
    char decimal[16] = "";
    int i, n, english = 0, arabic = 0;
    for (i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--help")) { fputs(usage, stdout); return EXIT_SUCCESS; }
        if (!strcmp(argv[i], "--style=auto")) auto_style = 1;
        else if (!strcmp(argv[i], "--style=plain")) auto_style = 0;
        else if (!strcmp(argv[i], "--lang=en")) english = 1;
        else if (!strcmp(argv[i], "--lang=fr")) english = 0;
        else if (!strcmp(argv[i], "--numerals=arabic")) arabic = 1;
        else if (!strcmp(argv[i], "--numerals=roman")) arabic = 0;
        else if (!strcmp(argv[i], "--format=table")) format = TABLE;
        else if (!strcmp(argv[i], "--format=line")) format = LINE;
        else if (!strcmp(argv[i], "--format=json")) format = JSON;
        else if (!strcmp(argv[i], "--decimal-time")) clock = 1;
        else if (!strcmp(argv[i], "--no-decimal-time")) clock = 0;
        else if (!strcmp(argv[i], "--month-gloss")) gloss = 1;
        else if (!strcmp(argv[i], "--no-month-gloss")) gloss = 0;
        else if (!arg && argv[i][0] != '-') arg = argv[i];
        else {
            fputs(usage, stderr);
            return EXIT_FAILURE;
        }
    }
    t = republicain_terminal();
    if (!auto_style) t.bold = t.utf8 = 0;
    if (!t.columns) {
        const char *cols = getenv("COLUMNS");
        char *end = NULL;
        long value = cols ? strtol(cols, &end, 10) : 0;
        t.columns = value > 0 && value <= 32767 && !*end ? (int)value : 80;
    }
    if (clock < 0) clock = !arg;
    if (clock && arg) {
        fputs("--decimal-time is for the current local date; omit YYYY-MM-DD.\n", stderr);
        return EXIT_FAILURE;
    }
    if (!arg && !republicain_now(&d, &seconds)) {
        fputs("Cannot read local date.\n", stderr);
        return EXIT_FAILURE;
    }
    if ((arg && !parse(arg, &d)) || !republicain_convert(d, &r)) {
        fputs("Expected a valid date from 1792-09-22 to 9999-12-31.\n", stderr);
        return EXIT_FAILURE;
    }
    n = r.ordinal;
    /* Bastille Day follows the civil anniversary: the storming predates
     * year I. The other observances belong to Republican month/day pairs. */
    greeting = d.month == 7 && d.day == 14 ? "Aux armes, citoyens!" :
               republicain_observance(n, r.year, english, format == JSON || t.utf8);
    format_year(year, r.year, arabic);
    if (n < 360) {
        int m = n / 30;
        strcpy(month, text(months[m], t.utf8));
        if (gloss)
            sprintf(month + strlen(month), " (%s)", english ? month_gloss_en[m] :
                    text(month_gloss_fr[m], t.utf8));
    }
    if (clock) {
        /* 100000 decimal seconds per 86400 ordinary seconds, rounded down. */
        long ticks = seconds * 125L / 108L;
        sprintf(decimal, "%d:%02d:%02d", (int)(ticks/10000), (int)(ticks/100%100), (int)(ticks%100));
        sprintf(time_label, "%s: %s", english ? "Decimal time" :
                 t.utf8 ? "Heure d\303\251cimale " : "Heure decimale ", decimal);
    }
    if (format == JSON) {
        json_date(d, r, english, year, gloss, clock ? decimal : NULL, greeting);
    } else if (format == TABLE) {
        /* Preserve the 13-column minimum for three bordered cells. */
        inset = t.columns >= 17 ? "  " : t.columns >= 15 ? " " : "";
        t.columns -= 2 * (int)strlen(inset);
        table(r, month, year, english, t, inset, time_label, greeting);
        putchar('\n');
    } else {
        const char *note = new_year_note(r, english, t.utf8);
        if (t.bold) fputs("\033[1m", stdout);
        if (n < 360)
            printf("%d %s", n%30+1, month);
        else if (english)
            printf("complementary day %d", n-359);
        else printf(t.utf8 ? "jour compl\303\251mentaire %d" :
                              "jour complementaire %d", n-359);
        fputs(english ? ", Year " : ", an ", stdout);
        fputs(year, stdout);
        if (t.bold) fputs("\033[0m", stdout);
        fputs(t.utf8 ? "  \342\200\224  " : "  -  ", stdout);
        dedication(n, english, t.utf8);
        if (clock) printf("  %s", time_label);
        if (greeting) printf("  %s", greeting);
        if (note) printf("  %s", note);
        putchar('\n');
    }
    return EXIT_SUCCESS;
}
