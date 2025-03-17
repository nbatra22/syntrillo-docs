cdk_diff_file='/tmp/cdk-diff.txt'

cat $cdk_diff_file |grep '\[+\] [0-9a-z]*\.zip$' |grep -o "[0-9a-z]\{64\}"