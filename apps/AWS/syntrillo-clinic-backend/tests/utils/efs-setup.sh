

mkdir efs
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-089ba2dcf3281033d.efs.us-east-1.amazonaws.com:/ efs

sudo chown -R ec2-user:ec2-user efs

cd efs
mkdir shared-python-modules

cd efs
mkdir shared-python-modules

cd shared-python-modules/
pip install -r requirements.txt --target .