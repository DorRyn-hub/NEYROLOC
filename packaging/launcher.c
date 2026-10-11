#include <unistd.h>
#include <stdlib.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>

/*
 * Minimal native launcher for the NEYROLOC NEW.app bundle.
 *
 * A shell script as CFBundleExecutable gets misdetected for architecture by
 * LaunchServices on this macOS version and crashes under Rosetta translation.
 * An AppleScript `do shell script` wrapper avoids that crash, but spawns
 * Python as a *child* process (applet -> /bin/sh -> python), so the running
 * GUI process is never actually the bundle's own process and macOS shows
 * "Python" in the menu bar/Dock instead of the app name.
 *
 * This binary is a real Mach-O executable (no arch-detection crash) that
 * execve()s directly into the venv's python, replacing itself in place
 * (same PID) so the LaunchServices identity assigned to this process at
 * launch time carries over to the interpreter that owns the window.
 */
int main(void) {
    const char *home = getenv("HOME");
    if (home != NULL) {
        char log_path[1024];
        snprintf(log_path, sizeof(log_path), "%s/Library/Logs/NEYROLOC_NEW.log", home);
        int fd = open(log_path, O_WRONLY | O_CREAT | O_TRUNC, 0644);
        if (fd >= 0) {
            dup2(fd, STDOUT_FILENO);
            dup2(fd, STDERR_FILENO);
            close(fd);
        }
    }

    if (home == NULL) {
        _exit(127);
    }
    char project_path[4096];
    char python_path[4096];
    const char *project_override = getenv("NEYROLOC_PROJECT_DIR");
    int project_length = project_override != NULL
        ? snprintf(project_path, sizeof(project_path), "%s", project_override)
        : snprintf(project_path, sizeof(project_path),
                   "%s/PycharmProjects/PycharmProjects/neyroloc_NEW", home);
    if (project_length < 0 || project_length >= (int)sizeof(project_path) || chdir(project_path) != 0) {
        _exit(127);
    }
    int python_length = snprintf(python_path, sizeof(python_path),
                                "%s/NEYROLOCK_5/.venv/bin/python", project_path);
    if (python_length < 0 || python_length >= (int)sizeof(python_path)) {
        _exit(127);
    }
    char *argv[] = {
        python_path,
        "main.py",
        NULL
    };
    execv(argv[0], argv);
    _exit(127);
}
