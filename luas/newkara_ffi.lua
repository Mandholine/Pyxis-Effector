	--ffi library
	
	local xffi = require("ffi")
	local advapix, pangocairo, fontconfig
	if xffi.os == "Windows" then
		advapix = xffi.load("Advapi32")
		xffi.cdef([[
		enum{CP_UTF8X2 = 65001};
		enum{MM_TEXT2X = 1};
		enum{TRANSPARENT2X = 1};
		enum{FW_NORMAL2X = 400, FW_BOLD2X = 700};
		enum{DEFAULT_CHARSET2X = 1};
		enum{OUT_TT_PRECIS2X = 4};
		enum{CLIP_DEFAULT_PRECIS2X = 0};
		enum{ANTIALIASED_QUALITY2X = 4};
		enum{DEFAULT_PITCH2X = 0x0};
		enum{FF_DONTCARE2X = 0x0};
		enum{PT_MOVETO2X = 0x6, PT_LINETO2X = 0x2, PT_BEZIERTO2X = 0x4, PT_CLOSEFIGURE2X = 0x1};
		typedef unsigned int UINT;
		typedef unsigned long DWORD;
		typedef DWORD* LPDWORD;
		typedef const char* LPCSTR;
		typedef const wchar_t* LPCWSTR;
		typedef wchar_t* LPWSTR;
		typedef char* LPSTR;
		typedef void* HANDLE;
		typedef HANDLE HDC;
		typedef int BOOL;
		typedef BOOL* LPBOOL;
		typedef unsigned int size_t;
		typedef HANDLE HFONT;
		typedef HANDLE HGDIOBJ;
		typedef long LONG;
		typedef wchar_t WCHAR;
		typedef unsigned char BYTE;
		typedef BYTE* LPBYTE;
		typedef int INT;
		typedef long LPARAM;
		static const int LF_FACESIZE2X = 32;
		static const int LF_FULLFACESIZE2X = 64;
		typedef struct{
			LONG tmHeight;
			LONG tmAscent;
			LONG tmDescent;
			LONG tmInternalLeading;
			LONG tmExternalLeading;
			LONG tmAveCharWidth;
			LONG tmMaxCharWidth;
			LONG tmWeight;
			LONG tmOverhang;
			LONG tmDigitizedAspectX;
			LONG tmDigitizedAspectY;
			WCHAR tmFirstChar;
			WCHAR tmLastChar;
			WCHAR tmDefaultChar;
			WCHAR tmBreakChar;
			BYTE tmItalic;
			BYTE tmUnderlined;
			BYTE tmStruckOut;
			BYTE tmPitchAndFamily;
			BYTE tmCharSet;
		}TEXTMETRICW, *LPTEXTMETRICW;
		typedef struct{
			LONG cx;
			LONG cy;
		}SIZE, *LPSIZE;
		typedef struct{
			LONG left;
			LONG top;
			LONG right;
			LONG bottom;
		}RECT;
		typedef const RECT* LPCRECT;
		typedef struct{
			LONG x;
			LONG y;
		}POINT, *LPPOINT;
		typedef struct{
		  LONG  lfHeight;
		  LONG  lfWidth;
		  LONG  lfEscapement;
		  LONG  lfOrientation;
		  LONG  lfWeight;
		  BYTE  lfItalic;
		  BYTE  lfUnderline;
		  BYTE  lfStrikeOut;
		  BYTE  lfCharSet;
		  BYTE  lfOutPrecision;
		  BYTE  lfClipPrecision;
		  BYTE  lfQuality;
		  BYTE  lfPitchAndFamily;
		  WCHAR lfFaceName[LF_FACESIZE2X];
		}LOGFONTW, *LPLOGFONTW;
		typedef struct{
		  LOGFONTW elfLogFont;
		  WCHAR   elfFullName[LF_FULLFACESIZE2X];
		  WCHAR   elfStyle[LF_FACESIZE2X];
		  WCHAR   elfScript[LF_FACESIZE2X];
		}ENUMLOGFONTEXW, *LPENUMLOGFONTEXW;
		enum{FONTTYPE_RASTER2X = 1, FONTTYPE_DEVICE2X = 2, FONTTYPE_TRUETYPE2X = 4};
		typedef int (__stdcall *FONTENUMPROC)(const ENUMLOGFONTEXW*, const void*, DWORD, LPARAM);
		enum{ERROR_SUCCESS2X = 0};
		typedef HANDLE HKEY;
		typedef HKEY* PHKEY;
		enum{HKEY_LOCAL_MACHINE2X = 0x80000002};
		typedef enum{KEY_READ2X = 0x20019}REGSAM;
		int MultiByteToWideChar(UINT, DWORD, LPCSTR, int, LPWSTR, int);
		int WideCharToMultiByte(UINT, DWORD, LPCWSTR, int, LPSTR, int, LPCSTR, LPBOOL);
		HDC CreateCompatibleDC(HDC);
		BOOL DeleteDC(HDC);
		int SetMapMode(HDC, int);
		int SetBkMode(HDC, int);
		size_t wcslen(const wchar_t*);
		HFONT CreateFontW(int, int, int, int, int, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD, LPCWSTR);
		HGDIOBJ SelectObject(HDC, HGDIOBJ);
		BOOL DeleteObject(HGDIOBJ);
		BOOL GetTextMetricsW(HDC, LPTEXTMETRICW);
		BOOL GetTextExtentPoint32W(HDC, LPCWSTR, int, LPSIZE);
		BOOL BeginPath(HDC);
		BOOL ExtTextOutW(HDC, int, int, UINT, LPCRECT, LPCWSTR, UINT, const INT*);
		BOOL EndPath(HDC);
		int GetPath(HDC, LPPOINT, LPBYTE, int);
		BOOL AbortPath(HDC);
		int EnumFontFamiliesExW(HDC, LPLOGFONTW, FONTENUMPROC, LPARAM, DWORD);
		LONG RegOpenKeyExA(HKEY, LPCSTR, DWORD, REGSAM, PHKEY);
		LONG RegCloseKey(HKEY);
		LONG RegEnumValueW(HKEY, DWORD, LPWSTR, LPDWORD, LPDWORD, LPDWORD, LPBYTE, LPDWORD);
		]])
	else
		pcall(function()
			pangocairo = xffi.load("pangocairo-1.0.so")
			xffi.cdef([[
			typedef enum{
				CAIRO_FORMAT_INVALID2   = -1,
				CAIRO_FORMAT_ARGB32X    = 0,
				CAIRO_FORMAT_RGB24X     = 1,
				CAIRO_FORMAT_A8X        = 2,
				CAIRO_FORMAT_A1X        = 3,
				CAIRO_FORMAT_RGB16_565X = 4,
				CAIRO_FORMAT_RGB30X     = 5
			}cairo_format_t;
			typedef void cairo_surface_t;
			typedef void cairo_t;
			typedef void PangoLayout;
			typedef void* gpointer;
			static const int PANGO_SCALE2 = 1024;
			typedef void PangoFontDescription;
			typedef enum{
				PANGO_WEIGHT_THIN2	= 100,
				PANGO_WEIGHT_ULTRALIGHT2 = 200,
				PANGO_WEIGHT_LIGHT2 = 300,
				PANGO_WEIGHT_NORMAL2 = 400,
				PANGO_WEIGHT_MEDIUM2 = 500,
				PANGO_WEIGHT_SEMIBOLD2 = 600,
				PANGO_WEIGHT_BOLD2 = 700,
				PANGO_WEIGHT_ULTRABOLD2 = 800,
				PANGO_WEIGHT_HEAVY2 = 900,
				PANGO_WEIGHT_ULTRAHEAVY2 = 1000
			}PangoWeight;
			typedef enum{
				PANGO_STYLE_NORMAL,
				PANGO_STYLE_OBLIQUE,
				PANGO_STYLE_ITALIC
			}PangoStyle;
			typedef void PangoAttrList;
			typedef void PangoAttribute;
			typedef enum{
				PANGO_UNDERLINE_NONE,
				PANGO_UNDERLINE_SINGLE,
				PANGO_UNDERLINE_DOUBLE,
				PANGO_UNDERLINE_LOW,
				PANGO_UNDERLINE_ERROR
			}PangoUnderline;
			typedef int gint;
			typedef gint gboolean;
			typedef void PangoContext;
			typedef unsigned int guint;
			typedef struct{
				guint ref_count;
				int ascent;
				int descent;
				int approximate_char_width;
				int approximate_digit_width;
				int underline_position;
				int underline_thickness;
				int strikethrough_position;
				int strikethrough_thickness;
			}PangoFontMetrics;
			typedef void PangoLanguage;
			typedef struct{
				int x;
				int y;
				int width;
				int height;
			}PangoRectangle;
			typedef enum{
				CAIRO_STATUS_SUCCESS2 = 0
			}cairo_status_t;
			typedef enum{
				CAIRO_PATH_MOVE_TO,
				CAIRO_PATH_LINE_TO,
				CAIRO_PATH_CURVE_TO,
				CAIRO_PATH_CLOSE_PATH
			}cairo_path_data_type_t;
			typedef union{
				struct{
					cairo_path_data_type_t type;
					int length;
				}header;
				struct{
					double x, y;
				}point;
			}cairo_path_data_t;
			typedef struct{
				cairo_status_t status;
				cairo_path_data_t* data;
				int num_data;
			}cairo_path_t;
			cairo_surface_t* cairo_image_surface_create(cairo_format_t, int, int);
			void cairo_surface_destroy(cairo_surface_t*);
			cairo_t* cairo_create(cairo_surface_t*);
			void cairo_destroy(cairo_t*);
			PangoLayout* pango_cairo_create_layout(cairo_t*);
			void g_object_unref(gpointer);
			PangoFontDescription* pango_font_description_new(void);
			void pango_font_description_free(PangoFontDescription*);
			void pango_font_description_set_family(PangoFontDescription*, const char*);
			void pango_font_description_set_weight(PangoFontDescription*, PangoWeight);
			void pango_font_description_set_style(PangoFontDescription*, PangoStyle);
			void pango_font_description_set_absolute_size(PangoFontDescription*, double);
			void pango_layout_set_font_description(PangoLayout*, PangoFontDescription*);
			PangoAttrList* pango_attr_list_new(void);
			void pango_attr_list_unref(PangoAttrList*);
			void pango_attr_list_insert(PangoAttrList*, PangoAttribute*);
			PangoAttribute* pango_attr_underline_new(PangoUnderline);
			PangoAttribute* pango_attr_strikethrough_new(gboolean);
			PangoAttribute* pango_attr_letter_spacing_new(int);
			void pango_layout_set_attributes(PangoLayout*, PangoAttrList*);
			PangoContext* pango_layout_get_context(PangoLayout*);
			const PangoFontDescription* pango_layout_get_font_description(PangoLayout*);
			PangoFontMetrics* pango_context_get_metrics(PangoContext*, const PangoFontDescription*, PangoLanguage*);
			void pango_font_metrics_unref(PangoFontMetrics*);
			int pango_font_metrics_get_ascent(PangoFontMetrics*);
			int pango_font_metrics_get_descent(PangoFontMetrics*);
			int pango_layout_get_spacing(PangoLayout*);
			void pango_layout_set_text(PangoLayout*, const char*, int);
			void pango_layout_get_pixel_extents(PangoLayout*, PangoRectangle*, PangoRectangle*);
			void cairo_save(cairo_t*);
			void cairo_restore(cairo_t*);
			void cairo_scale(cairo_t*, double, double);
			void pango_cairo_layout_path(cairo_t*, PangoLayout*);
			void cairo_new_path(cairo_t*);
			cairo_path_t* cairo_copy_path(cairo_t*);
			void cairo_path_destroy(cairo_path_t*);
			]])
		end)
		pcall(function()
			fontconfig = xffi.load("fontconfig")
			xffi.cdef([[
			typedef void FcConfig;
			typedef void FcPattern;
			typedef struct{
				int nobject;
				int sobject;
				const char** objects;
			}FcObjectSet;
			typedef struct{
				int nfont;
				int sfont;
				FcPattern** fonts;
			}FcFontSet;
			typedef enum{
				FcResultMatch,
				FcResultNoMatch,
				FcResultTypeMismatch,
				FcResultNoId,
				FcResultOutOfMemory
			}FcResult;
			typedef unsigned char FcChar8;
			typedef int FcBool;
			FcConfig* FcInitLoadConfigAndFonts(void);
			FcPattern* FcPatternCreate(void);
			void FcPatternDestroy(FcPattern*);
			FcObjectSet* FcObjectSetBuild(const char*, ...);
			void FcObjectSetDestroy(FcObjectSet*);
			FcFontSet* FcFontList(FcConfig*, FcPattern*, FcObjectSet*);
			void FcFontSetDestroy(FcFontSet*);
			FcResult FcPatternGetString(FcPattern*, const char*, int, FcChar8**);
			FcResult FcPatternGetBool(FcPattern*, const char*, int, FcBool*);
			]])
		end)
	end
	
	return {["ffi"] = xffi, ["advapix"] = advapix, ["pangocairo"] = pangocairo, ["fontconfig"] = fontconfig}