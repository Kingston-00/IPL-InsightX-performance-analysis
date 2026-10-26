"""IPL InsightX - analytics helpers for historical IPL data."""
import os

# Keeps NumPy's memory use small on computers with little free RAM (no effect on results).
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
