#!/usr/bin/env python3
"""
prerequisites.py

Install system and Python prerequisites for running `pp.py` in Colab (or Debian-based Linux).

Usage in Colab:
  !python prerequisites.py

The script attempts to install system packages (Firefox + geckodriver) and Python packages
(pandas, selenium, openpyxl). It is idempotent and prints progress.
"""

import os
import subprocess
import sys


def run(cmd, **kwargs):
    print("=>", " ".join(cmd) if isinstance(cmd, (list, tuple)) else cmd)
    subprocess.check_call(cmd, **kwargs)


def install_system_packages():
    # Update apt and install Firefox + geckodriver (Debian/Ubuntu/Colab)
    try:
        run(["apt-get", "update", "-y"])
        run(["apt-get", "install", "-y", "firefox", "geckodriver", "xvfb"])
    except subprocess.CalledProcessError:
        print("System package installation failed. You may need to run manually or check permissions.")


def install_python_packages():
    # Use the current Python interpreter to install packages
    pkgs = ["--upgrade", "pip", "setuptools"]
    run([sys.executable, "-m", "pip", "install"] + pkgs)

    required = ["pandas", "selenium", "openpyxl"]
    run([sys.executable, "-m", "pip", "install"] + required)


def main():
    print("Preparing environment for pp.py")

    # Detect likely Colab environment
    in_colab = False
    try:
        import google.colab  # type: ignore
        in_colab = True
    except Exception:
        in_colab = False

    if in_colab:
        print("Detected Colab environment — installing apt and pip packages (may take a few minutes)")
        install_system_packages()
    else:
        print("Not running in Colab. Only installing Python packages. For system packages, run the commands in the repo 'prerequisites' file.")

    install_python_packages()

    print("\nDone. Next steps:")
    print(" - Ensure 'config.json' exists and set 'automation_allowed': true")
    print(" - Upload 'PiratePunisher_WebsiteList.xlsx' to the Colab working directory")
    print(" - Run: python pp.py")


if __name__ == '__main__':
    main()
