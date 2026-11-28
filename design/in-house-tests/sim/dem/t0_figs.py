"""Queue wrapper so the job scheduler counts figure rendering as a job: python t0_figs.py run <figures.py args>"""
import sys
import figures

if __name__ == "__main__":
    sys.argv = ["figures.py"] + sys.argv[2:]
    which = sys.argv[1:]
    figures.main(which) if hasattr(figures, "main") else None
