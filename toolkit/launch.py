"""Starts Lifekeeper as a package. The release workflow builds the Windows and Mac apps from this file."""
import sys

from lifekeeper.app import main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "faces":  # "Lifekeeper faces scan EXPORTS": the faces add-on from the app
        from lifekeeper.faces import main as faces_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        faces_main()
    else:
        main()
