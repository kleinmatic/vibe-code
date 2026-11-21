# Prospective native port: keep `make TARGET=ultrix` as its build entry point.
# Use the ISO C fallback until terminal capabilities are verified on Ultrix.
TERMINAL = shared/adapters/plain_terminal.c
