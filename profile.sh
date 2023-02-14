python -m cProfile -o output.pstats aspmc/main.py "$@"
gprof2dot -f pstats output.pstats | dot -Tpng -o output.png
xdg-open output.png
