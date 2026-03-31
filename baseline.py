"""Backward-compatible baseline entrypoint.

Delegates execution to the evaluator-facing root script in inference.py.
"""

from inference import main


if __name__ == "__main__":
    main()
