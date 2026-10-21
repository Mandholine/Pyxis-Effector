/**
 * libass_profiler - Native Subtitle Rendering Performance Benchmark
 * 
 * Clean-room native reimplementation of libass_profiler based on reverse
 * engineering of the original Windows PE64 binary.
 * 
 * Measures frame-by-frame subtitle rasterisation load using libass:
 * - Render duration per frame (high-resolution monotonic timers).
 * - Total bitmap memory allocated across glyphs/shapes.
 * - Largest single bitmap allocation in frame.
 * - Total image object count.
 * 
 * Supports: Linux, macOS, FreeBSD, and Windows (native compilation without Wine).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ass/ass.h>

#if defined(_WIN32) || defined(_WIN64)
    #include <windows.h>
    static double get_time_seconds(void) {
        static LARGE_INTEGER frequency;
        static int initialized = 0;
        if (!initialized) {
            QueryPerformanceFrequency(&frequency);
            initialized = 1;
        }
        LARGE_INTEGER counter;
        QueryPerformanceCounter(&counter);
        return (double)counter.QuadPart / (double)frequency.QuadPart;
    }
#elif defined(__APPLE__)
    #include <time.h>
    #include <mach/mach_time.h>
    static double get_time_seconds(void) {
        struct timespec ts;
        clock_gettime(CLOCK_MONOTONIC, &ts);
        return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
    }
#else
    #include <time.h>
    static double get_time_seconds(void) {
        struct timespec ts;
        clock_gettime(CLOCK_MONOTONIC, &ts);
        return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
    }
#endif

/**
 * Format milliseconds into standard ASS timestamp notation: H:MM:SS.mmm
 * Exactly matching the format string "%01d:%02d:%02d.%03d" from the original binary.
 */
static void format_timestamp(long long ms, char *buffer, size_t buffer_size) {
    if (ms < 0) ms = 0;
    long long h = ms / 3600000;
    long long rem = ms % 3600000;
    long long m = rem / 60000;
    rem = rem % 60000;
    long long s = rem / 1000;
    long long frac_ms = rem % 1000;
    snprintf(buffer, buffer_size, "%01d:%02d:%02d.%03d", (int)h, (int)m, (int)s, (int)frac_ms);
}

/**
 * Calculate the overall track duration in milliseconds by inspecting the maximum
 * end timestamp (Start + Duration) across all subtitle events.
 */
static long long compute_track_duration_ms(ASS_Track *track) {
    long long max_end = 0;
    if (!track) return 0;
    for (int i = 0; i < track->n_events; i++) {
        ASS_Event *ev = &track->events[i];
        long long end_time = (long long)ev->Start + (long long)ev->Duration;
        if (end_time > max_end) {
            max_end = end_time;
        }
    }
    return max_end;
}

static void print_usage(const char *prog_name, const char *default_output) {
    printf("libass version %d\n", ass_library_version());
    printf("Usage: %s <assfile> <output> [--fps <val>]\n", prog_name);
    printf("output is optional and defaults to %s\n", default_output);
}

int main(int argc, char **argv) {
    const char *default_output = "output.csv";
    float fps = 23.976f;

    if (argc < 2) {
        print_usage("libass_profiler", default_output);
        return 1;
    }

    const char *ass_path = argv[1];
    const char *output_csv = default_output;

    // Optional argument parsing
    int arg_idx = 2;
    while (arg_idx < argc) {
        if (strcmp(argv[arg_idx], "--fps") == 0 && arg_idx + 1 < argc) {
            fps = (float)atof(argv[arg_idx + 1]);
            if (fps <= 0.0f) fps = 23.976f;
            arg_idx += 2;
        } else if (argv[arg_idx][0] != '-') {
            output_csv = argv[arg_idx];
            arg_idx++;
        } else {
            arg_idx++;
        }
    }

    // 1. Initialise libass library
    ASS_Library *library = ass_library_init();
    if (!library) {
        fprintf(stderr, "[libass_profiler] Error: Failed to initialise libass library context.\n");
        return 1;
    }

    // Enable embedded font extraction from ASS script headers ([Fonts] section)
    ass_set_extract_fonts(library, 1);

    // 2. Read ASS subtitle track
    ASS_Track *track = ass_read_file(library, (char *)ass_path, NULL);
    if (!track) {
        fprintf(stderr, "[libass_profiler] Error: Failed to load subtitle file: '%s'\n", ass_path);
        ass_library_done(library);
        return 1;
    }

    // 3. Initialise libass renderer
    ASS_Renderer *renderer = ass_renderer_init(library);
    if (!renderer) {
        fprintf(stderr, "[libass_profiler] Error: Failed to initialise libass renderer.\n");
        ass_free_track(track);
        ass_library_done(library);
        return 1;
    }

    // Determine canvas frame size (from PlayResX/Y or fallback to 384x288)
    int frame_w = track->PlayResX > 0 ? track->PlayResX : 384;
    int frame_h = track->PlayResY > 0 ? track->PlayResY : 288;
    ass_set_frame_size(renderer, frame_w, frame_h);
    ass_set_storage_size(renderer, frame_w, frame_h);

    // Configure font provider and fallback family
    ass_set_fonts(renderer, NULL, "Sans", ASS_FONTPROVIDER_AUTODETECT, NULL, 1);

    // 4. Open output CSV
    FILE *out = fopen(output_csv, "w");
    if (!out) {
        fprintf(stderr, "[libass_profiler] Error: Unable to open output CSV file: '%s'\n", output_csv);
        ass_free_track(track);
        ass_renderer_done(renderer);
        ass_library_done(library);
        return 1;
    }

    // Header exactly matches libass_profiler.exe protocol
    fprintf(out, "%s\n", ass_path);
    fprintf(out, "time,total_image_size,largest_image_size,image_count,time_benchmark\n");

    long long total_duration_ms = compute_track_duration_ms(track);
    int frame_index = 0;
    long long current_time_ms = 0;
    char time_str[32];

    // Main telemetry rendering loop
    while (current_time_ms < total_duration_ms) {
        format_timestamp(current_time_ms, time_str, sizeof(time_str));

        double t_start = get_time_seconds();
        int detect_change = 0;
        ASS_Image *img = ass_render_frame(renderer, track, current_time_ms, &detect_change);
        double time_benchmark = get_time_seconds() - t_start;

        long long total_image_size = 0;
        long long largest_image_size = 0;
        long long image_count = 0;

        // Traverse linked list of rendered raster images
        while (img) {
            // Formula extracted from original disassembly: (h - 1) * stride + w
            long long size = (img->h > 0 && img->w > 0)
                ? ((long long)(img->h - 1) * img->stride + img->w)
                : 0;

            total_image_size += size;
            if (size > largest_image_size) {
                largest_image_size = size;
            }
            image_count++;
            img = img->next;
        }

        fprintf(out, "%s,%lld,%lld,%lld,%lf\n",
                time_str, total_image_size, largest_image_size, image_count, time_benchmark);

        frame_index++;
        current_time_ms = (long long)roundf((float)frame_index * (1000.0f / fps));
    }

    // Cleanup resources
    fclose(out);
    ass_free_track(track);
    ass_renderer_done(renderer);
    ass_library_done(library);

    return 0;
}
