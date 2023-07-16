#! /bin/bash
#  Script to set up services for the camera.

pushd $(dirname $0) > /dev/null

ROOT=$(realpath ./)


# Install services to /etc/systemd/system, inserting the correct directory path.

if [ ! -f /etc/systemd/system/my-gps.service ] ; then
	cp  gps/my-gps.service  /etc/systemd/system/
	sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-gps.service
fi

if [ ! -f /etc/systemd/system/my-cam.service ] ; then
	cp  cam/my-cam.service  /etc/systemd/system/
	sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-cam.service
fi

systemctl daemon-reload
systemctl enable my-gps
systemctl enable my-cam
systemctl start  my-gps
systemctl start  my-cam


# Append a mapping for the external SSD to /etc/fstab if it is not already there.

if [ ! -d /media/Camera ] ; then
	mkdir /media/Camera
fi

if ! fgrep /dev/sd  /etc/fstab ; then
	echo "" >> /etc/fstab
	echo "# Add a fixed mount point for our external SSD" >> /etc/fstab
	echo "/dev/sda1  /media/Camera   auto  users,noauto  0  2" >> /etc/fstab
fi


popd > /dev/null
