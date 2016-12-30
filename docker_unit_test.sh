#!/bin/bash
#CHANGE ME
SRC_SVN_URL=https://10.5.72.70:8443/power/ZXDE50_CL01_V1.0/trunk/esmu/src
#CHANGE ME
MEMBERS_ID="10064088 10072341 10114492 10164269 00190995"
#10072341 chenzhen
#10114492 wangyong
#10164269 wulaiqiang
#00190995 longmingxing

export UNIT_TEST_SCRIPT=unittest/scripts
cd ${WORKSPACE}/${UNIT_TEST_SCRIPT}
export PATH=/usr/sbin:${PATH}
./clean.sh
./test.sh all junit
COV_ALL="python ${WORKSPACE}/${UNIT_TEST_SCRIPT}/coveragediff.py -t ${DIFF_START_DATE} -s ${SRC_SVN_URL}"
${COV_ALL}
echo "coverage all finish!"

for user in ${MEMBERS_ID};do
COV_USER="${COV_ALL} -u ${user}"
${COV_USER}
echo "coverage diff finish~"
done
