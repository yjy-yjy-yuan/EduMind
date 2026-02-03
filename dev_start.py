"""
Dev launcher for EduMind (backend + frontend).

Goals:
- One command to create/use Python venv for backend
- Install backend/frontend deps (optional)
- Start backend (FastAPI/Uvicorn) + optional Celery worker + Vite dev server
- Open browser when ready
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_VENV_DIR = BACKEND_DIR / ".venv"


def is_windows() -> bool:
    return os.name == "nt"


def venv_python_path(venv_dir: Path) -> Path:
    if is_windows():
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def which(cmd: str) -> str | None:
    from shutil import which as _which

    return _which(cmd)


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    printable = " ".join(argv)
    print(f"[run] {printable}")
    return subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        check=check,
    )


def ensure_backend_venv(venv_dir: Path) -> Path:
    python_in_venv = venv_python_path(venv_dir)
    if python_in_venv.exists():
        return python_in_venv

    print(f"[info] Creating venv: {venv_dir}")
    run([sys.executable, "-m", "venv", str(venv_dir)], cwd=BACKEND_DIR)

    python_in_venv = venv_python_path(venv_dir)
    if not python_in_venv.exists():
        raise RuntimeError(f"Venv created but python not found: {python_in_venv}")
    return python_in_venv


def pip_install(python_exe: Path, requirements_file: Path) -> None:
    run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], cwd=BACKEND_DIR)
    run([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)], cwd=BACKEND_DIR)


def npm_install(frontend_dir: Path) -> None:
    npm = which("npm") or which("npm.cmd")
    if not npm:
        raise RuntimeError("npm not found; please install Node.js 16+ and ensure npm is on PATH")
    run([npm, "install"], cwd=frontend_dir)


def wait_for_port(host: str, port: int, *, timeout_s: float) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def start_process(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
) -> subprocess.Popen[object]:
    printable = " ".join(argv)
    print(f"[start] {printable}")
    if is_windows():
        # New process group lets us send CTRL_BREAK_EVENT for a clean shutdown.
        return subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # type: ignore[attr-defined]
        )
    return subprocess.Popen(argv, cwd=str(cwd), env=env)


def stop_process(proc: subprocess.Popen[object], *, name: str) -> None:
    if proc.poll() is not None:
        return
    print(f"[stop] {name}")

    try:
        if is_windows():
            proc.send_signal(signal.CTRL_BREAK_EVENT)  # type: ignore[attr-defined]
            proc.wait(timeout=8)
        else:
            proc.terminate()
            proc.wait(timeout=8)
    except Exception:
        proc.kill()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="One-command dev launcher (backend + frontend).")
    p.add_argument("--skip-install", action="store_true", help="Skip pip/npm install steps")
    p.add_argument("--no-backend", action="store_true", help="Do not start backend")
    p.add_argument("--no-frontend", action="store_true", help="Do not start frontend")
    celery_group = p.add_mutually_exclusive_group()
    celery_group.add_argument("--celery", action="store_true", help="Start Celery worker (requires Redis)")
    celery_group.add_argument(
        "--no-celery",
        action="store_true",
        help="(deprecated) Same as default: do not start Celery worker",
    )
    p.add_argument("--open", action="store_true", help="Open browser automatically")
    p.add_argument("--api-url", default="http://localhost:5001", help="Backend API base URL")
    p.add_argument("--web-url", default="http://localhost:5173", help="Frontend dev URL")
    p.add_argument("--backend-wait", type=float, default=30.0, help="Seconds to wait for backend port")
    p.add_argument("--frontend-wait", type=float, default=60.0, help="Seconds to wait for frontend port")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if not BACKEND_DIR.exists():
        print("[error] backend/ not found; please run from repo root")
        return 2
    if not FRONTEND_DIR.exists():
        print("[error] frontend/ not found; please run from repo root")
        return 2

    venv_python = ensure_backend_venv(BACKEND_VENV_DIR)

    if not args.skip_install:
        pip_install(venv_python, BACKEND_DIR / "requirements.txt")
        npm_install(FRONTEND_DIR)

    env_base = os.environ.copy()

    procs: list[tuple[str, subprocess.Popen[object]]] = []
    try:
        if not args.no_backend:
            backend_env = env_base.copy()
            # Ensure backend reads backend/.env by using cwd=backend.
            backend_proc = start_process([str(venv_python), "run.py"], cwd=BACKEND_DIR, env=backend_env)
            procs.append(("backend", backend_proc))

            if not wait_for_port("127.0.0.1", 5001, timeout_s=args.backend_wait):
                print("[warn] Backend port 5001 not ready yet; continuing anyway")

        if not args.no_backend and bool(getattr(args, "celery", False)):
            celery_env = env_base.copy()
            celery_proc = start_process(
                [str(venv_python), "-m", "celery", "-A", "celery_app", "worker", "--loglevel=info"],
                cwd=BACKEND_DIR,
                env=celery_env,
            )
            procs.append(("celery", celery_proc))

        if not args.no_frontend:
            npm = which("npm") or which("npm.cmd")
            if not npm:
                raise RuntimeError("npm not found; please install Node.js 16+ and ensure npm is on PATH")

            frontend_env = env_base.copy()
            frontend_env["VITE_API_BASE_URL"] = args.api_url
            frontend_proc = start_process([npm, "run", "dev"], cwd=FRONTEND_DIR, env=frontend_env)
            procs.append(("frontend", frontend_proc))

            if wait_for_port("127.0.0.1", 5173, timeout_s=args.frontend_wait):
                print(f"[ready] {args.web_url}")
                if args.open:
                    webbrowser.open(args.web_url)
            else:
                print("[warn] Frontend port 5173 not ready yet; open the URL manually when it is ready")

        if args.open and args.no_frontend:
            webbrowser.open(args.web_url)

        print("[info] Press Ctrl+C to stop.")
        while True:
            time.sleep(0.5)
            for name, proc in list(procs):
                code = proc.poll()
                if code is not None:
                    if name == "celery":
                        print(f"[warn] celery exited with code {code}; continuing without worker")
                        procs = [(n, p) for (n, p) in procs if p is not proc]
                        continue
                    print(f"[exit] {name} exited with code {code}")
                    return int(code) if isinstance(code, int) else 1
    except KeyboardInterrupt:
        print("\n[info] Stopping...")
        return 0
    finally:
        for name, proc in reversed(procs):
            stop_process(proc, name=name)


if __name__ == "__main__":
    raise SystemExit(main())
