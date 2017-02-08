NUM=0
FROMNUM=0
SERVERIP=''

if [ "$#" -eq "2" ];then
    PRODIR=$1
    PROCMD=$2
else
    echo "Usage: `basename $0` first second"
    echo "You provided $# parameters,but 2 are required."
    exit 1
fi

echo $PRODIR
echo $PROCMD

ln -s /home/libg/Jx3Robot/Jx3Robot/libEngine_Lua5D.so /lib/libEngine_Lua5D.so

cd $PRODIR

$PROCMD
#cd /home/libg/Jx3Robot/Jx3Robot/
#./Jx3RobotD  -T SuperRobot:$NUM    -a LBG -r 排站    -l    -k 随机 -j 随机 -g 随机  -s $SERVERIP -p $FROMNUM

#/home/libg/Jx3Robot/Jx3Robot/Jx3RobotD  -T SuperRobot:100    -a LBG -r 排站    -l    -k 随机 -j 随机 -g 随机  -s 10.20.96.155 -p 1 
#/home/libg/Jx3Robot/Jx3Robot/Jx3RobotD  -T SuperRobot:$NUM    -a LBG -r 排站    -l    -k 随机 -j 随机 -g 随机  -s $SERVERIP -p $FROMNUM 

while [ 1 = 1 ]
do
    sleep 10
done 

