"""Nimbus OS theme helpers (shared by nimbus-welcome, nimbus-menubar and nimbus-dock).

Settings live in ~/.config/nimbus/theme.json:
  {"dark": false, "accent": "#3478f6", "light_effects": false, "welcome_done": false}
"""
import configparser
import json
import os
import re
import shutil
import subprocess

CONF = os.path.expanduser("~/.config/nimbus/theme.json")
GTK_CSS = os.path.expanduser("~/.config/gtk-3.0/gtk.css")
GTK_INI = os.path.expanduser("~/.config/gtk-3.0/settings.ini")
MARK_BEGIN, MARK_END = "/* >>> nimbus-theme (managed, do not edit) >>> */", "/* <<< nimbus-theme <<< */"

ACCENTS = [("Blue", "#3478f6"), ("Purple", "#8e5cf6"), ("Pink", "#f06292"), ("Red", "#e5484d"),
           ("Orange", "#f5a623"), ("Green", "#34c759"), ("Graphite", "#8e8e93")]
DEFAULT = {"dark": False, "accent": "#3478f6", "light_effects": False, "welcome_done": False}
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
VM_NAMES = {"kvm": "KVM", "qemu": "QEMU", "oracle": "VirtualBox", "vmware": "VMware", "microsoft": "Hyper-V",
            "xen": "Xen", "parallels": "Parallels", "bochs": "Bochs", "bhyve": "bhyve", "zvm": "z/VM", "uml": "User-mode Linux"}


def dry():
    return bool(os.environ.get("NIMBUS_DRY_RUN"))


def load():
    t = dict(DEFAULT)
    try:
        with open(CONF) as f:
            data = json.load(f)
        for k in DEFAULT:
            if k in data:
                t[k] = data[k]
    except Exception:
        pass
    t["dark"] = bool(t["dark"]); t["light_effects"] = bool(t["light_effects"]); t["welcome_done"] = bool(t["welcome_done"])
    if not (isinstance(t["accent"], str) and HEX.match(t["accent"])):
        t["accent"] = DEFAULT["accent"]
    return t


def save(t):
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    with open(CONF, "w") as f:
        json.dump({k: t.get(k, DEFAULT[k]) for k in DEFAULT}, f, indent=1)


def run(cmd, timeout=5):
    if dry():
        print("DRY:", " ".join(cmd))
        return ""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def xfconf(channel, prop, value, typ="string"):
    if shutil.which("xfconf-query") or dry():
        run(["xfconf-query", "-c", channel, "-p", prop, "-n", "-t", typ, "-s", str(value).lower() if typ == "bool" else str(value)])


def rgb(hexcolor):
    h = hexcolor.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def gtk_css(t):
    a = t["accent"]; r, g, b = rgb(a)
    return """%s
@define-color nimbus_accent %s;
selection, *:selected, row:selected, .view:selected, menuitem:hover, modelbutton:hover { background-color: @nimbus_accent; color: #ffffff; }
button.suggested-action, button.suggested-action:hover, button.suggested-action:active { background-image: none; background-color: @nimbus_accent; border-color: @nimbus_accent; color: #ffffff; }
switch:checked { background-image: none; background-color: @nimbus_accent; border-color: @nimbus_accent; }
check:checked, radio:checked { background-image: none; background-color: @nimbus_accent; border-color: @nimbus_accent; color: #ffffff; }
scale highlight, progressbar progress, levelbar block.filled { background-image: none; background-color: @nimbus_accent; }
entry:focus, spinbutton:focus { border-color: @nimbus_accent; box-shadow: 0 0 0 1px rgba(%d,%d,%d,0.45); }
link, *:link { color: @nimbus_accent; }
%s
""" % (MARK_BEGIN, a, r, g, b, MARK_END)


def _merge_block(path, block):
    old = ""
    try:
        with open(path) as f:
            old = f.read()
    except Exception:
        pass
    s, e = old.find(MARK_BEGIN), old.find(MARK_END)
    if s != -1 and e != -1:
        old = old[:s] + old[e + len(MARK_END):]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(old.strip() + ("\n\n" if old.strip() else "") + block)


def write_gtk(t):
    _merge_block(GTK_CSS, gtk_css(t))
    cp = configparser.ConfigParser()
    cp.optionxform = str
    try:
        cp.read(GTK_INI)
    except Exception:
        pass
    if not cp.has_section("Settings"):
        cp.add_section("Settings")
    cp.set("Settings", "gtk-application-prefer-dark-theme", "1" if t["dark"] else "0")
    os.makedirs(os.path.dirname(GTK_INI), exist_ok=True)
    with open(GTK_INI, "w") as f:
        cp.write(f)


def apply(t):
    """Save the theme and apply it to the running desktop."""
    save(t)
    write_gtk(t)
    xfconf("xsettings", "/Net/ThemeName", "Arc-Dark" if t["dark"] else "Arc")
    xfconf("xsettings", "/Net/IconThemeName", "Papirus-Dark" if t["dark"] else "Papirus")
    xfconf("xfwm4", "/general/theme", "Arc-Dark" if t["dark"] else "Arc")
    xfconf("xfwm4", "/general/show_frame_shadow", not t["light_effects"], "bool")
    xfconf("xfwm4", "/general/show_popup_shadow", not t["light_effects"], "bool")
    if shutil.which("pkill") or dry():                    # tell the menu bar and dock to re-read the theme
        run(["pkill", "-USR1", "-f", "nimbus-menubar"]); run(["pkill", "-USR1", "-f", "nimbus-dock"])


def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return ""


def detect_vm():
    """-> (is_virtual_machine, name)"""
    v = run(["systemd-detect-virt"]).strip().lower()
    if v and v != "none":
        return True, VM_NAMES.get(v, v)
    probe = (read("/sys/class/dmi/id/product_name") + " " + read("/sys/class/dmi/id/sys_vendor")).lower()
    for key, name in (("virtualbox", "VirtualBox"), ("vmware", "VMware"), ("qemu", "QEMU"), ("kvm", "KVM"),
                      ("virtual machine", "Hyper-V"), ("bochs", "Bochs")):
        if key in probe:
            return True, name
    if re.search(r"^flags\s*:.*\bhypervisor\b", read("/proc/cpuinfo"), re.M):
        return True, "a hypervisor"
    return False, ""


def internet_state():
    """-> 'online' | 'limited' | 'offline' | 'unknown'"""
    out = run(["nmcli", "networking", "connectivity", "check"], timeout=12).strip().lower()
    return {"full": "online", "limited": "limited", "portal": "limited", "none": "offline"}.get(out, "unknown")
