#ifndef REPUBLICAIN_TERMINAL_H
#define REPUBLICAIN_TERMINAL_H
struct terminal { int bold, utf8, columns; };
struct terminal republicain_terminal(void);
#endif
