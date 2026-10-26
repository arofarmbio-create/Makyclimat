import subprocess, sys, traceback
out = []
try:
    r = subprocess.run([sys.executable, "scripts/validate_landslides.py", "--country", "mdg"], capture_output=True, text=True, timeout=1500)
    out.append(r.stdout[-5000:] + r.stderr[-3000:])
except Exception:
    out.append(traceback.format_exc())
open("data/_probe.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
