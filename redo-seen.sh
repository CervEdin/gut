#!/bin/sh
# next..seen
case "$#,$1" in
1,-u|1,-d)
	exec Meta/Reintegrate "$1" "$0"
esac
Meta/Reintegrate "$@" <<\EOF
93befde20386a71ec2cc63e52bde494b314204df pick CONTRIBUTING: add contribution guide
07d323b2c45a37efb74fe47f876f88c0adf2fec3 pick Revert "CONTRIBUTING: add contribution guide"
EOF
