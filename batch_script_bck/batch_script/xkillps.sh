ps aux | grep 01gwac_backup | awk '{print($2)}'>listkill
for pad in `cat listkill`
do
	kill -9 $pad
done
rm -rf listkill 
echo "over"
ps aux | grep 01gwac
