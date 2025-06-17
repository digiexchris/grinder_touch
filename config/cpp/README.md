sudo apt install binutils-dev libdw-dev libunwind-19-dev libunwind-19 clang cmake ninja-build ccache lld

this version requires 2.10+,
http://buildbot2.highlab.com/debian/dists/bookworm/master-uspace/binary-amd64/

deb http://buildbot2.highlab.com/debian/ bookworm master-uspace

when it releases:

deb http://buildbot2.highlab.com/debian/ bookworm 2.10-uspace


echo 'deb [arch=amd64] https://gnipsel.com/flexgui/apt-repo stable main' | sudo tee /etc/apt/sources.list.d/flexgui.list
sudo curl --silent --show-error https://gnipsel.com/flexgui/apt-repo/pgp-key.public -o /etc/apt/trusted.gpg.d/flexgui.asc