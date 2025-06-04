mkdir efs
sudo yum -y install nfs-utils

FILE_SYSTEM_ID=""
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport $FILE_SYSTEM_ID.efs.us-east-1.amazonaws.com:/ efs

pip install pipdeptree
