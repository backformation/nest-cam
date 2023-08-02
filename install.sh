#! /bin/bash
#  Script to set up services for the camera.

pushd $(dirname $0) > /dev/null

ROOT=$(realpath ./)


# Provide a place to save video data.

if [ ! -d /media/Camera ] ; then
	mkdir /media/Camera
fi


# Install services to /etc/systemd/system, inserting the correct directory path.

if [ ! -f /etc/systemd/system/my-gps.service ] ; then
	cp  code/my-gps.service  /etc/systemd/system/
	sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-gps.service
fi

if [ ! -f /etc/systemd/system/my-cam.service ] ; then
	cp  code/my-cam.service  /etc/systemd/system/
	sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-cam.service
fi

systemctl daemon-reload
systemctl enable my-gps
systemctl enable my-cam
systemctl start  my-gps
systemctl start  my-cam


popd > /dev/null
