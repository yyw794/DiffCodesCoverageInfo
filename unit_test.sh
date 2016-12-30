#!/bin/bash
MOUNT="/share"
CONTAINER_ID=`docker ps -a | grep $CONTAINER | awk '{print $1}'`
if [ -n "$CONTAINER_ID" ];then
    docker rm -f $CONTAINER_ID
fi

docker run --rm --name=$CONTAINER --net=host -i -e "WORKSPACE=${MOUNT}" -e "DIFF_START_DATE=$DIFF_START_DATE" -v ${WORKSPACE}:${MOUNT} $DOCKER /bin/bash ${MOUNT}/${SCRIPT}/docker_unit_test.sh
