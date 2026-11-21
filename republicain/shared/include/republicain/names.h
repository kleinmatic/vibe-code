#ifndef REPUBLICAIN_NAMES_H
#define REPUBLICAIN_NAMES_H
struct name { const char *plain, *utf8; };
extern const struct name rural[360], months[12], weekdays[10], festivals[6];
extern const char *const rural_en[360];
const char *republicain_observance(int ordinal, int year, int english, int utf8);
extern const struct name month_gloss_fr[12];
extern const char *const month_gloss_en[12];
#endif
