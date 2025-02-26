#!/bin/bash

##NOTE AWK & GREP REPORT NO STDOUT IF NO MATCHES ARE FOUND (AWK DO NOT PRODUCE ANY OUTPUT)

#PARAM $1 is ref targets file
#PARAM $2 is var targets file
#PARAM $3 is job_id
dir=$(dirname $1)

#common targets extraction
LC_ALL=C sort -u -T "$dir" $1 >$1.sort.txt
LC_ALL=C sort -u -T "$dir" $2 >$2.sort.txt
# cp $2.sort.txt $3.common_targets.txt
LC_ALL=C comm -12 $1.sort.txt $2.sort.txt >$3.common_targets.txt

#Semi common targets extraction
LC_ALL=C awk '{print $4"\t"$5"\t"$6}' $1.sort.txt >$3.ref.chr_pos.txt
LC_ALL=C awk 'NR==FNR{a[$0]; next} {if ($4"\t"$5"\t"$6 in a) print $0}' $3.ref.chr_pos.txt $2.sort.txt >$3.semi_common_targets.txt

#Aggiungo i target del ref: ora semicommon contiene: target con iupac e targets senza iupac corrispondenti;
# target senza iupac del var e corrispondenti target senza iupac del ref
LC_ALL=C awk 'NR==FNR{a[$0]; next} ($4"\t"$5"\t"$6) in a' $3.ref.chr_pos.txt $1.sort.txt >>$3.semi_common_targets.txt
LC_ALL=C sort -u -T "$dir" $3.semi_common_targets.txt >$3.semi_common_targets.sort.txt

#unique variant targets extraction
LC_ALL=C comm -13 $3.semi_common_targets.sort.txt $2.sort.txt >$3.unique_targets.txt

mv $3.semi_common_targets.sort.txt $3.semi_common_targets.txt
#Remove tmp files, NOTE maybe keep first two and change name to $1 and $2 ?
rm $1.sort.txt $2.sort.txt $3.ref.chr_pos.txt
