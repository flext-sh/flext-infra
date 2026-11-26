/*
 * Capture outcomes in the qualified native process boundary.
 * Copyright (c) 2026 FLEXT Team. All rights reserved.
 * SPDX-License-Identifier: MIT
 */

#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/un.h>
#include <unistd.h>

static void report(const char *name, long result)
{
    int observed = result < 0 ? errno : 0;
    printf("%s=%d\n", name, observed);
}

static void ring_probes(void)
{
    report("io_uring_setup", syscall(SYS_io_uring_setup, 0, NULL));
    report("io_uring_enter", syscall(SYS_io_uring_enter, -1, 0, 0, 0, NULL, 0));
    report("io_uring_register", syscall(SYS_io_uring_register, -1, 0, NULL, 0));
}

static void readonly_probes(void)
{
    int pair[2];
    report("socket", socket(AF_UNIX, SOCK_STREAM, 0));
    report("socketpair", socketpair(AF_UNIX, SOCK_STREAM, 0, pair));
    report("connect", connect(-1, NULL, 0));
    report("bind", bind(-1, NULL, 0));
    report("listen", listen(-1, 0));
    report("accept", accept(-1, NULL, NULL));
    report("accept4", accept4(-1, NULL, NULL, 0));
    report("sendto", sendto(-1, NULL, 0, 0, NULL, 0));
    report("recvfrom", recvfrom(-1, NULL, 0, 0, NULL, NULL));
    report("sendmsg", sendmsg(-1, NULL, 0));
    report("recvmsg", recvmsg(-1, NULL, 0));
    /* A libc wrapper can return before entering the kernel for zero messages. */
    report("sendmmsg", syscall(SYS_sendmmsg, -1, NULL, 0, 0));
    report("recvmmsg", recvmmsg(-1, NULL, 0, 0, NULL));
}

static int fixture_probes(void)
{
    struct sockaddr_un external = {
        .sun_family = AF_UNIX, .sun_path = "/probe/outside.sock"
    };
    struct sockaddr_un internal = {
        .sun_family = AF_UNIX, .sun_path = "/probe/inside.sock"
    };
    int client = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    int listener = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (client < 0 || listener < 0) {
        perror("fixture socket");
        return 1;
    }
    if (bind(listener, (const struct sockaddr *)&internal, sizeof(internal)) ||
        listen(listener, 1)) {
        perror("fixture listener");
        return 1;
    }
    report("connect:external-pathname",
           connect(client, (const struct sockaddr *)&external, sizeof(external)));
    report("connect:fixture-pathname",
           connect(client, (const struct sockaddr *)&internal, sizeof(internal)));
    int pair[2];
    report("socket:non-unix", socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0));
    report("socketpair:non-unix",
           socketpair(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0, pair));
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fputs("a process isolation probe requires its declared profile\n", stderr);
        return 1;
    }
    if (strcmp(argv[1], "fixture") == 0) {
        if (fixture_probes() != 0) {
            return 1;
        }
    } else if (strcmp(argv[1], "read-only") == 0) {
        readonly_probes();
    } else {
        fputs("unknown native isolation profile\n", stderr);
        return 1;
    }
    ring_probes();
    return fflush(stdout) != 0;
}
