import logging
from os import path

from watchgod import PythonWatcher

from uvicorn.supervisors.basereload import BaseReload

logger = logging.getLogger("uvicorn.error")


class CustomWatcher(PythonWatcher):
    pass


class WatchGodReload(BaseReload):
    def __init__(self, config, target, sockets):
        super().__init__(config, target, sockets)
        self.reloader_name = "watchgod"
        self.watchers = []
        watch_dirs = {
            path.realpath(watch_dir)
            for watch_dir in self.config.reload_dirs
            if path.isdir(watch_dir)
        }
        watch_dirs_set = set(watch_dirs)

        # remove directories that already have a parent watched, so that we don't have
        # duplicated change events
        for watch_dir in watch_dirs:
            for compare_dir in watch_dirs:
                if compare_dir is watch_dir:
                    continue

                if watch_dir.startswith(compare_dir) and len(watch_dir) > len(
                    compare_dir
                ):
                    watch_dirs_set.remove(watch_dir)
        self.watch_dir_set = watch_dirs_set
        for w in watch_dirs_set:
            self.watchers.append(CustomWatcher(w))

    def should_restart(self):
        for watcher in self.watchers:
            change = watcher.check()
            if change != set():
                message = "Detected file change in '%s'. Reloading..."
                logger.warning(message, [c[1] for c in change])
                return True

        return False
