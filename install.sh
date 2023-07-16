#! /bin/bash
#  Script to set up services for the camera.

pushd $(dirname $0) > /dev/null

ROOT=$(realpath ./)

# Install services to /etc/systemd/system, inserting the correct directory path.

if [ ! -f /etc/systemd/system/my-gps.service ] ; then
	cp  gps/my-gps.service  /etc/systemd/system/
	sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-gps.service
fi

systemctl daemon-reload
systemctl enable my-gps
systemctl start  my-gps

popd > /dev/null
