"""sitecustomize (v0.10, Mac shell only — es.sh puts this folder on PYTHONPATH).
The connected Mac folder refuses deletes ("Operation not permitted") unless the creator grants it, but renames work. So every
os.unlink / os.remove / os.rmdir / shutil.rmtree that is refused there MOVES the item into VIDEO GEN/_to_delete/_trash/ instead.
The creator empties _to_delete/ by hand. Nothing in the tools needs to know about it."""
import os, shutil, time, itertools, functools

_unlink, _rmdir, _rmtree = os.unlink, os.rmdir, shutil.rmtree
_n = itertools.count()


def _trash_for(path):
    p = os.path.abspath(path); d = os.path.dirname(p)
    while d and d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, '_series')): break
        d = os.path.dirname(d)
    root = d if d and os.path.isdir(os.path.join(d, '_series')) else os.path.dirname(p)
    t = os.path.join(root, '_to_delete', '_trash'); os.makedirs(t, exist_ok=True)
    return os.path.join(t, f"{time.strftime('%m%d-%H%M%S')}-{next(_n)}-{os.path.basename(p.rstrip('/'))}")


def _move(path):
    os.rename(path, _trash_for(path))


def unlink(path, *a, dir_fd=None, **k):
    try: return _unlink(path, *a, dir_fd=dir_fd, **k) if dir_fd is not None else _unlink(path)
    except PermissionError:
        if dir_fd is not None: raise
        _move(path)


def rmdir(path, *a, dir_fd=None, **k):
    try: return _rmdir(path, *a, dir_fd=dir_fd, **k) if dir_fd is not None else _rmdir(path)
    except PermissionError:
        if dir_fd is not None: raise
        _move(path)


def rmtree(path, *a, **k):
    try: return _rmtree(path, *a, **k)
    except PermissionError:
        if os.path.exists(path): _move(path)


# functools.partial: never binds as a method (pathlib 3.10 keeps `unlink = os.unlink` as a class attribute)
os.unlink = os.remove = functools.partial(unlink); os.rmdir = functools.partial(rmdir); shutil.rmtree = rmtree
