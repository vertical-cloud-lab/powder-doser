/* Let Bambu Studio's GLX-built GLEW initialise on GLFW's OSMesa context (Wayland/headless): fake the few GLX
   calls glewInit makes, and hand GL entry points out from OSMesa. */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <GL/osmesa.h>
typedef void (*fp)(void);
static int fake_display;
void *glXGetCurrentDisplay(void) { return &fake_display; }
void *glXGetCurrentContext(void) { return (void *)OSMesaGetCurrentContext(); }
int glXQueryVersion(void *d, int *maj, int *min) { if (maj) *maj = 1; if (min) *min = 4; return 1; }
const char *glXGetClientString(void *d, int name) { return ""; }
const char *glXQueryExtensionsString(void *d, int s) { return ""; }
const char *glXQueryServerString(void *d, int s, int n) { return ""; }
static fp lookup(const unsigned char *name) {
    if (strncmp((const char *)name, "glX", 3) == 0) return (fp)dlsym(RTLD_DEFAULT, (const char *)name);
    return (fp)OSMesaGetProcAddress((const char *)name);
}
fp glXGetProcAddressARB(const unsigned char *name) { return lookup(name); }
fp glXGetProcAddress(const unsigned char *name) { return lookup(name); }
