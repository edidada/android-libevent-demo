#ifdef __ANDROID__
#include <android/log.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "libevent_demo", __VA_ARGS__)
#else
#define LOGI(...) printf(__VA_ARGS__)
#endif

#include <event2/event.h>
#include <cstdio>
#include <cstdlib>

static int timer_count = 0;

static void timer_cb(evutil_socket_t fd, short what, void* arg) {
    (void)fd;
    (void)what;
    timer_count++;
    LOGI("timer fired #%d\n", timer_count);
    if (timer_count >= 3) {
        struct event_base* base = (struct event_base*)arg;
        event_base_loopbreak(base);
    }
}

int main() {
    LOGI("libevent demo start, version=%s\n", event_get_version());
    printf("libevent version: %s\n", event_get_version());

    struct event_base* base = event_base_new();
    if (!base) {
        LOGI("event_base_new failed\n");
        return 1;
    }
    LOGI("using method: %s\n", event_base_get_method(base));

    struct event* ev = event_new(base, -1, EV_PERSIST, timer_cb, base);
    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = 500000;  // 0.5s
    event_add(ev, &tv);

    LOGI("entering event loop...\n");
    event_base_dispatch(base);

    event_free(ev);
    event_base_free(base);
    LOGI("libevent demo done\n");
    printf("libevent demo done\n");
    return 0;
}
