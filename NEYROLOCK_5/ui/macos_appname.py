"""Заставить macOS показывать имя приложения в строке меню, а не «Python».

Приложение запускается из .app-бандла, но интерпретатор python.org
перезапускает себя внутри `Python.framework/.../Python.app`, поэтому
`[[NSBundle mainBundle]]` указывает на этот вложенный Python.app, и AppKit
берёт из него `CFBundleName` = "Python" для меню приложения.

infoDictionary у mainBundle — мутабельный (`__NSDictionaryM`), так что до
создания NSApplication (то есть до QApplication) можно подменить в нём
`CFBundleName` на наше имя. Это чистый рантайм-приём через ctypes, без
внешних зависимостей вроде pyobjc.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import sys


def set_app_name(name: str) -> None:
    """Подменить CFBundleName в mainBundle. No-op вне macOS / при ошибке."""
    if sys.platform != "darwin":
        return
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]

        def msg(restype, receiver, selector, *args):
            argtypes = [ctypes.c_void_p, ctypes.c_void_p] + [type(a) for a in args]
            objc.objc_msgSend.restype = restype
            objc.objc_msgSend.argtypes = argtypes
            return objc.objc_msgSend(receiver, objc.sel_registerName(selector), *args)

        def nsstring(text: str):
            ns_cls = objc.objc_getClass(b"NSString")
            return msg(
                ctypes.c_void_p,
                ns_cls,
                b"stringWithUTF8String:",
                ctypes.c_char_p(text.encode("utf-8")),
            )

        ns_bundle = objc.objc_getClass(b"NSBundle")
        main_bundle = msg(ctypes.c_void_p, ns_bundle, b"mainBundle")
        if not main_bundle:
            return
        info = msg(ctypes.c_void_p, main_bundle, b"infoDictionary")
        if not info:
            return
        msg(
            ctypes.c_void_p,
            info,
            b"setObject:forKey:",
            ctypes.c_void_p(nsstring(name)),
            ctypes.c_void_p(nsstring("CFBundleName")),
        )
    except Exception:
        # Косметика — при любой ошибке просто оставляем как есть.
        pass
