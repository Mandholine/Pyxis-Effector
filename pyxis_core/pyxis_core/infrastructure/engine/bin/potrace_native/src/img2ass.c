/* Copyright (C) 2026 Pyxis Effector contributors.
   Native Image to ASSDraw Vector Shape Converter using potracelib + stb_image.
   Pure C, zero Python, zero external CLI dependencies.
   
   Conforms to: Pyxis Technical Specification — Section 12: Shape/IMG to Shape */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include "potracelib.h"

#define BM_WORDSIZE ((int)sizeof(potrace_word))
#define BM_WORDBITS (8 * BM_WORDSIZE)
#define BM_HIBIT (((potrace_word)1) << (BM_WORDBITS - 1))
#define bm_scanline(bm, y) ((bm)->map + (y) * (bm)->dy)
#define bm_index(bm, x, y) (&bm_scanline(bm, y)[(x) / BM_WORDBITS])
#define bm_mask(x) (BM_HIBIT >> ((x) & (BM_WORDBITS - 1)))
#define bm_range(x, a) ((int)(x) >= 0 && (int)(x) < (a))
#define bm_safe(bm, x, y) (bm_range(x, (bm)->w) && bm_range(y, (bm)->h))
#define BM_USET(bm, x, y) (*bm_index(bm, x, y) |= bm_mask(x))
#define BM_UCLR(bm, x, y) (*bm_index(bm, x, y) &= ~bm_mask(x))
#define BM_UPUT(bm, x, y, b) ((b) ? BM_USET(bm, x, y) : BM_UCLR(bm, x, y))
#define BM_PUT(bm, x, y, b) (bm_safe(bm, x, y) ? BM_UPUT(bm, x, y, b) : 0)

static potrace_bitmap_t *bm_new(int w, int h) {
    potrace_bitmap_t *bm;
    int dy = (w + BM_WORDBITS - 1) / BM_WORDBITS;

    bm = (potrace_bitmap_t *)malloc(sizeof(potrace_bitmap_t));
    if (!bm) return NULL;
    bm->w = w;
    bm->h = h;
    bm->dy = dy;
    bm->map = (potrace_word *)calloc(h, dy * BM_WORDSIZE);
    if (!bm->map) {
        free(bm);
        return NULL;
    }
    return bm;
}

static void bm_free(potrace_bitmap_t *bm) {
    if (bm != NULL) {
        free(bm->map);
    }
    free(bm);
}

static void print_ass_curve(FILE *fout, potrace_curve_t *curve, double width, double height, double scale, int center, double off_x, double off_y) {
    int m = curve->n;
    if (m == 0) return;

    double cx = center ? (width / 2.0) : 0.0;
    double cy = center ? (height / 2.0) : 0.0;

    /* Start point */
    potrace_dpoint_t *c = curve->c[m - 1];
    long start_x = (long)round((c[2].x - cx) * scale + off_x);
    long start_y = (long)round(((height - c[2].y) - cy) * scale + off_y);
    fprintf(fout, "m %ld %ld ", start_x, start_y);

    for (int i = 0; i < m; i++) {
        c = curve->c[i];
        if (curve->tag[i] == POTRACE_CORNER) {
            long p1x = (long)round((c[1].x - cx) * scale + off_x);
            long p1y = (long)round(((height - c[1].y) - cy) * scale + off_y);
            long p2x = (long)round((c[2].x - cx) * scale + off_x);
            long p2y = (long)round(((height - c[2].y) - cy) * scale + off_y);
            fprintf(fout, "l %ld %ld l %ld %ld ", p1x, p1y, p2x, p2y);
        } else if (curve->tag[i] == POTRACE_CURVETO) {
            long p0x = (long)round((c[0].x - cx) * scale + off_x);
            long p0y = (long)round(((height - c[0].y) - cy) * scale + off_y);
            long p1x = (long)round((c[1].x - cx) * scale + off_x);
            long p1y = (long)round(((height - c[1].y) - cy) * scale + off_y);
            long p2x = (long)round((c[2].x - cx) * scale + off_x);
            long p2y = (long)round(((height - c[2].y) - cy) * scale + off_y);
            fprintf(fout, "b %ld %ld %ld %ld %ld %ld ", p0x, p0y, p1x, p1y, p2x, p2y);
        }
    }
}

static void render_ass_tree(FILE *fout, potrace_path_t *tree, double width, double height, double scale, int center, double off_x, double off_y) {
    for (potrace_path_t *p = tree; p; p = p->sibling) {
        print_ass_curve(fout, &p->curve, width, height, scale, center, off_x, off_y);
        for (potrace_path_t *q = p->childlist; q; q = q->sibling) {
            print_ass_curve(fout, &q->curve, width, height, scale, center, off_x, off_y);
        }
        for (potrace_path_t *q = p->childlist; q; q = q->sibling) {
            render_ass_tree(fout, q->childlist, width, height, scale, center, off_x, off_y);
        }
    }
}

static void print_usage(const char *prog) {
    printf("img2ass — Native Shape/IMG to Shape Converter (Pyxis Effector Specification)\n");
    printf("Uso: %s <imagen> [salida.ass] [opciones]\n\n", prog);
    printf("Parámetros (conforme a Documentación Técnica Pyxis — Sección 12):\n");
    printf("  --bin_mode <luminance|silhouette> Modo de binarización (defecto: luminance)\n");
    printf("  --anchor <center|origin>          Punto de anclaje cartesiano (defecto: center)\n");
    printf("  --threshold <0-255>               Umbral de luminancia o corte (defecto: 128)\n");
    printf("  --tolerance <float>               Simplificación de curvas / turdsize (defecto: 1.0)\n");
    printf("  --alphamax <float>                Suavizado de esquinas (defecto: 1.0)\n");
    printf("  --opttoler <float>                Tolerancia de optimización Bézier (defecto: 0.2)\n");
    printf("  --scale <factor>                  Factor multiplicador de escala (defecto: 1.0)\n");
    printf("  --pos <x> <y>                     Posición cartesiana \\pos(x, y) en pantalla (defecto: 960 540)\n");
    printf("  --offset <x> <y>                  Desplazamiento adicional de vértices en px (defecto: 0 0)\n");
    printf("  --invert                          Invertir polaridad de primer plano / fondo\n");
    printf("  --raw                             Imprimir sólo la cadena vectorial ASSDraw ('m ... b ...')\n");
}

int main(int argc, char **argv) {
    if (argc < 2) {
        print_usage(argv[0]);
        return 1;
    }

    const char *img_path = argv[1];
    const char *output_file = NULL;

    /* Default values matching Pyxis Shape/IMG to Shape specification */
    int threshold = 128;
    int alpha_threshold = 10;
    double tolerance = 1.0;
    double alphamax = 1.0;
    double opttoler = 0.2;
    double scale = 1.0;
    double offset_x = 0.0;
    double offset_y = 0.0;
    int pos_x = 960;
    int pos_y = 540;
    int center = 1;
    int invert = 0;
    int raw_mode = 0;
    int is_silhouette = 0;

    for (int i = 2; i < argc; i++) {
        if ((strcmp(argv[i], "--threshold") == 0) && i + 1 < argc) {
            threshold = atoi(argv[++i]);
        } else if ((strcmp(argv[i], "--bin_mode") == 0 || strcmp(argv[i], "--bin-mode") == 0) && i + 1 < argc) {
            const char *bm = argv[++i];
            if (strcmp(bm, "silhouette") == 0 || strcmp(bm, "alpha") == 0) {
                is_silhouette = 1;
            }
        } else if (strcmp(argv[i], "--anchor") == 0 && i + 1 < argc) {
            const char *anc = argv[++i];
            if (strcmp(anc, "origin") == 0 || strcmp(anc, "topleft") == 0) {
                center = 0;
            } else {
                center = 1;
            }
        } else if (strcmp(argv[i], "--tolerance") == 0 && i + 1 < argc) {
            tolerance = atof(argv[++i]);
        } else if (strcmp(argv[i], "--alphamax") == 0 && i + 1 < argc) {
            alphamax = atof(argv[++i]);
        } else if (strcmp(argv[i], "--opttoler") == 0 && i + 1 < argc) {
            opttoler = atof(argv[++i]);
        } else if (strcmp(argv[i], "--scale") == 0 && i + 1 < argc) {
            scale = atof(argv[++i]);
        } else if (strcmp(argv[i], "--pos") == 0 && i + 2 < argc) {
            pos_x = atoi(argv[++i]);
            pos_y = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--offset") == 0 && i + 2 < argc) {
            offset_x = atof(argv[++i]);
            offset_y = atof(argv[++i]);
        } else if (strcmp(argv[i], "--invert") == 0) {
            invert = 1;
        } else if (strcmp(argv[i], "--raw") == 0) {
            raw_mode = 1;
        } else if (argv[i][0] != '-' && output_file == NULL) {
            output_file = argv[i];
        }
    }

    /* 1. Cargar imagen con stb_image (PNG, JPG, BMP, WebP) */
    int w, h, channels;
    unsigned char *data = stbi_load(img_path, &w, &h, &channels, 4);
    if (!data) {
        fprintf(stderr, "Error: No se pudo cargar la imagen '%s': %s\n", img_path, stbi_failure_reason());
        return 1;
    }

    /* 2. Crear mapa de bits Potrace con lógica idéntica a Pyxis img_tracer_engine */
    potrace_bitmap_t *bm = bm_new(w, h);
    if (!bm) {
        fprintf(stderr, "Error: Fallo de memoria al asignar mapa de bits\n");
        stbi_image_free(data);
        return 1;
    }

    int any_fg = 0;
    for (int y = 0; y < h; y++) {
        int y_bm = h - 1 - y;
        for (int x = 0; x < w; x++) {
            unsigned char *px = data + (y * w + x) * 4;
            unsigned char r = px[0];
            unsigned char g = px[1];
            unsigned char b = px[2];
            unsigned char a = px[3];

            int is_fg = 0;
            if (is_silhouette) {
                is_fg = (a >= alpha_threshold) ? 1 : 0;
            } else {
                /* Luminance binarization with alpha gating */
                if (a >= alpha_threshold) {
                    int gray = (int)(0.299 * r + 0.587 * g + 0.114 * b);
                    is_fg = (gray < threshold) ? 1 : 0;
                }
            }

            if (invert) {
                is_fg = !is_fg;
            }

            if (is_fg) any_fg = 1;
            BM_PUT(bm, x, y_bm, is_fg);
        }
    }

    /* Fallback Pyxis: si ningún píxel coincide, usar silueta alfa */
    if (!any_fg && !is_silhouette) {
        for (int y = 0; y < h; y++) {
            int y_bm = h - 1 - y;
            for (int x = 0; x < w; x++) {
                unsigned char *px = data + (y * w + x) * 4;
                unsigned char a = px[3];
                int is_fg = (a >= alpha_threshold) ? 1 : 0;
                if (invert) is_fg = !is_fg;
                BM_PUT(bm, x, y_bm, is_fg);
            }
        }
    }
    stbi_image_free(data);

    /* 3. Ejecutar trazado vectorial Potrace */
    potrace_param_t *param = potrace_param_default();
    param->turdsize = (int)fmax(0.0, tolerance);
    param->alphamax = (alphamax > 1.33) ? 1.33 : (alphamax < 0.0 ? 0.0 : alphamax);
    param->opticurve = 1;
    param->opttolerance = (opttoler < 0.0) ? 0.0 : opttoler;

    potrace_state_t *st = potrace_trace(param, bm);
    bm_free(bm);
    potrace_param_free(param);

    if (!st || st->status != POTRACE_STATUS_OK) {
        fprintf(stderr, "Error: Falló la vectorización con Potrace\n");
        return 1;
    }

    /* 4. Emitir salida ASS o raw */
    FILE *fout = stdout;
    int is_file = 0;
    if (output_file) {
        fout = fopen(output_file, "w");
        if (!fout) {
            fprintf(stderr, "Error: No se pudo crear el archivo '%s'\n", output_file);
            fout = stdout;
        } else {
            is_file = 1;
        }
    }

    if (raw_mode) {
        render_ass_tree(fout, st->plist, (double)w, (double)h, scale, center, offset_x, offset_y);
        fprintf(fout, "\n");
    } else if (is_file) {
        fprintf(fout, "[Script Info]\n");
        fprintf(fout, "; Script generado conforme a Pyxis Effector — Sección 12: Shape/IMG to Shape\n");
        fprintf(fout, "Title: %s\n", img_path);
        fprintf(fout, "ScriptType: v4.00+\n");
        fprintf(fout, "WrapStyle: 0\n");
        fprintf(fout, "ScaledBorderAndShadow: yes\n");
        fprintf(fout, "PlayResX: 1920\n");
        fprintf(fout, "PlayResY: 1080\n\n");

        fprintf(fout, "[V4+ Styles]\n");
        fprintf(fout, "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n");
        fprintf(fout, "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,10,10,10,1\n\n");

        fprintf(fout, "[Events]\n");
        fprintf(fout, "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n");
        /* Tag estándar exacto de Sección 12.6 de la Documentación: {\p1\pos(X,Y)\1c&HFFFFFF&\bord0} */
        fprintf(fout, "Dialogue: 0,0:00:00.00,0:00:10.00,Default,,0,0,0,,{\\p1\\pos(%d,%d)\\1c&HFFFFFF&\\bord0}", pos_x, pos_y);
        render_ass_tree(fout, st->plist, (double)w, (double)h, scale, center, offset_x, offset_y);
        fprintf(fout, "{\\p0}\n");
        fclose(fout);

        printf("[OK] Archivo ASS generado exitosamente conforme a Sección 12 en: %s\n", output_file);
    } else {
        printf("{\\p1\\pos(%d,%d)\\1c&HFFFFFF&\\bord0}", pos_x, pos_y);
        render_ass_tree(fout, st->plist, (double)w, (double)h, scale, center, offset_x, offset_y);
        printf("{\\p0}\n");
    }

    potrace_state_free(st);
    return 0;
}
