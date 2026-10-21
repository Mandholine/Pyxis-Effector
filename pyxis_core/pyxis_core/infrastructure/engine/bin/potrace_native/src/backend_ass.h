/* Copyright (C) 2026 Pyxis Effector contributors.
   Aegisub / ASSDraw backend for Potrace. */

#ifndef BACKEND_ASS_H
#define BACKEND_ASS_H

#include <stdio.h>
#include "potracelib.h"
#include "main.h"

int page_ass(FILE *fout, potrace_path_t *plist, imginfo_t *imginfo);

#endif /* BACKEND_ASS_H */
