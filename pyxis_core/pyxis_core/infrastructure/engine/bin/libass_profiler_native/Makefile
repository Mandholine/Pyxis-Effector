# Makefile for libass_profiler (Linux & macOS)

CC ?= gcc
CFLAGS ?= -O3 -Wall -Wextra -std=c99
PKG_CONFIG ?= pkg-config

# Auto-detect libass compilation and linker flags
LIBASS_CFLAGS := $(shell $(PKG_CONFIG) --cflags libass 2>/dev/null || echo "")
LIBASS_LIBS   := $(shell $(PKG_CONFIG) --libs libass 2>/dev/null || echo "-lass")

# Math library
LDFLAGS ?= -lm $(LIBASS_LIBS)

TARGET = libass_profiler
SRC = libass_profiler.c

.PHONY: all clean install

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(LIBASS_CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f $(TARGET) *.o

# Install directly into PyxisNodes bin directory if available
install: $(TARGET)
	@if [ -d "../../Version en desarrollo/PyxisNodes/bin" ]; then \
		cp $(TARGET) "../../Version en desarrollo/PyxisNodes/bin/"; \
		echo "Installed $(TARGET) to PyxisNodes/bin/"; \
	else \
		echo "Target bin directory not found. Binary ready at ./$(TARGET)"; \
	fi
