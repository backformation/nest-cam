#! /bin/bash
#  Script to set up services for the camera.

pushd $(dirname $0) > /dev/null

ROOT=$(realpath ./)


# Provide a place to save video data.

mkdir -p /media/Camera
setfacl -dm o:rwX,m:rwX /media/Camera
setfacl -m  o:rwX,m:rwX /media/Camera


# Install services to /etc/systemd/system, inserting the correct directory path.

cp  code/my-gps.service  /etc/systemd/system/
sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-gps.service

cp  code/my-cam.service  /etc/systemd/system/
sed -i "s|ROOT|${ROOT}|g"  /etc/systemd/system/my-cam.service

systemctl daemon-reload
systemctl enable my-gps
systemctl enable my-cam
systemctl start  my-gps
systemctl start  my-cam


popd > /dev/null
