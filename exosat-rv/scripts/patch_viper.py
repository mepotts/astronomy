"""Make viper importable headlessly: it calls gnuplot at module-import time.

viper only needs gnuplot for interactive -look* plots, which an RV extraction never uses,
but the calls sit in class bodies so they fire on `import` and take the whole package down
where gnuplot is absent. Both are wrapped rather than removed, so a machine that does have
gnuplot keeps the original behaviour.
"""

import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/home/matth/viper-src")
p = root / "utils" / "gplot.py"
s = p.read_text(encoding="utf-8")
changed = 0

old_ver = """   version = subprocess.check_output(['gnuplot', '-V'])
   version = float(version.split()[1])"""
new_ver = """   # PATCHED (exosat-rv): gnuplot absent; only needed for interactive -look* plots.
   try:
      version = float(subprocess.check_output(['gnuplot', '-V']).split()[1])
   except Exception:
      version = 5.4"""
if old_ver in s:
    s = s.replace(old_ver, new_ver)
    changed += 1

for line in s.splitlines():
    if line.strip().startswith("_jsdir = subprocess.check_output"):
        indent = line[: len(line) - len(line.lstrip())]
        new = (
            f"{indent}# PATCHED (exosat-rv): see the note on Gplot.version.\n"
            f"{indent}try:\n"
            f"{indent}   {line.strip()}\n"
            f"{indent}except Exception:\n"
            f"{indent}   _jsdir = ''"
        )
        s = s.replace(line, new)
        changed += 1
        break

p.write_text(s, encoding="utf-8")
print(f"patched {p} ({changed} sites)")
