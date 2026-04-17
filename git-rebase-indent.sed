#!/usr/bin/sed -f

/^l.*/,/^l.*/s_^[^l].*_\t&_g
