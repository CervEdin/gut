#!/usr/bin/sed -f
/^l.*/,/^l.*/s_^[^l].*_\t\0_g
