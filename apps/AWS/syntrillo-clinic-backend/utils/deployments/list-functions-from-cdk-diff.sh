cdk_diff_file='/tmp/cdk-diff.txt'

cat $cdk_diff_file |grep 'AWS::Lambda::Function' |grep -o ".*/.*/.* " | cut -d'/' -f3