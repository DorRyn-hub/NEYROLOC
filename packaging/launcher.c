#include <mach-o/dyld.h>

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Native launcher for the NEYROLOC NEW local macOS bundle.
 *
 * build_app.sh puts both the application sources and its virtual environment
 * under Contents/Resources.  Resolving them from this executable makes the
 * bundle independent from the checkout's absolute path.  The copied venv may
 * still depend on the Python.framework installed on the Mac that built it;
 * build_app.sh documents and validates that deliberate local-bundle limit.
 */

static void redirect_logs(void) {
    const char *home = getenv("HOME");
    if (home == NULL) {
        return;
    }

    char log_path[PATH_MAX];
    int written = snprintf(
        log_path,
        sizeof(log_path),
        "%s/Library/Logs/NEYROLOC_NEW.log",
        home
    );
    if (written < 0 || (size_t)written >= sizeof(log_path)) {
        return;
    }

    int fd = open(log_path, O_WRONLY | O_CREAT | O_APPEND, 0600);
    if (fd >= 0) {
        dup2(fd, STDOUT_FILENO);
        dup2(fd, STDERR_FILENO);
        close(fd);
    }
}

static void fail(const char *message, const char *detail) {
    fprintf(stderr, "NEYROLOC launcher: %s", message);
    if (detail != NULL) {
        fprintf(stderr, ": %s", detail);
    }
    fprintf(stderr, "\n");
    fflush(stderr);

    /* Finder hides stderr, so also show a short actionable native dialog. */
    execl(
        "/usr/bin/osascript",
        "osascript",
        "-e",
        "display alert \"NEYROLOC NEW\" message \"Локальное Python-окружение недоступно. Пересоберите приложение на этом Mac. Подробности: ~/Library/Logs/NEYROLOC_NEW.log\"",
        (char *)NULL
    );
    _exit(127);
}

static int resource_paths(
    char *app_dir,
    size_t app_dir_size,
    char *python_path,
    size_t python_path_size,
    char *main_path,
    size_t main_path_size
) {
    char executable[PATH_MAX];
    uint32_t executable_size = (uint32_t)sizeof(executable);
    if (_NSGetExecutablePath(executable, &executable_size) != 0) {
        return -1;
    }

    char resolved[PATH_MAX];
    if (realpath(executable, resolved) == NULL) {
        return -1;
    }
    char *slash = strrchr(resolved, '/');
    if (slash == NULL) {
        return -1;
    }
    *slash = '\0'; /* .../Contents/MacOS */

    int app_written = snprintf(
        app_dir,
        app_dir_size,
        "%s/../Resources/app",
        resolved
    );
    int python_written = snprintf(
        python_path,
        python_path_size,
        "%s/../Resources/venv/bin/python",
        resolved
    );
    int main_written = snprintf(
        main_path,
        main_path_size,
        "%s/../Resources/app/main.py",
        resolved
    );
    if (app_written < 0 || (size_t)app_written >= app_dir_size
            || python_written < 0 || (size_t)python_written >= python_path_size
            || main_written < 0 || (size_t)main_written >= main_path_size) {
        return -1;
    }
    return 0;
}

int main(int argc, char *argv[]) {
    redirect_logs();

    char app_dir[PATH_MAX];
    char python_path[PATH_MAX];
    char main_path[PATH_MAX];
    if (resource_paths(
            app_dir,
            sizeof(app_dir),
            python_path,
            sizeof(python_path),
            main_path,
            sizeof(main_path)
        ) != 0) {
        fail("cannot resolve app bundle resources", strerror(errno));
    }

    if (access(python_path, X_OK) != 0) {
        fail("bundled venv Python is missing or its external Python.framework is unavailable", python_path);
    }
    if (access(main_path, R_OK) != 0) {
        fail("bundled main.py is missing", main_path);
    }
    if (chdir(app_dir) != 0) {
        fail("cannot enter bundled application directory", app_dir);
    }

    /* Do not create __pycache__ inside the signed application bundle. */
    setenv("PYTHONDONTWRITEBYTECODE", "1", 0);
    setenv("PYTHONNOUSERSITE", "1", 0);

    char **child_argv = calloc((size_t)argc + 2, sizeof(char *));
    if (child_argv == NULL) {
        fail("cannot allocate launcher arguments", NULL);
    }
    child_argv[0] = python_path;
    child_argv[1] = main_path;
    for (int i = 1; i < argc; ++i) {
        child_argv[i + 1] = argv[i];
    }

    execv(python_path, child_argv);
    fail("cannot start bundled Python", strerror(errno));
    return 127;
}
