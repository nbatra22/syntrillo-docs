

mkdir efs
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport fs-089ba2dcf3281033d.efs.us-east-1.amazonaws.com:/ efs

sudo chown ec2-user:ec2-user efs

cd efs
mkdir shared-python-modules

cd efs
mkdir shared-python-modules

cd shared-python-modules/
pip install -r requirements.txt --target .


# ON Amazon Linux Bastion
sudo yum install docker
sudo systemctl start docker
sudo chmod 666 /var/run/docker.sock
sudo usermod -a -G docker ec2-user
docker run --rm -v "$PWD":/app -w /app python:3.10 pip install --no-cache-dir -r requirements.txt --target=.
docker run --rm -v "$PWD":/app -w /app python:3.12 pip install --no-cache-dir -r requirements.txt --target=. --upgrade

# INSTALL PIP
sudo yum update
sudo yum install python3-pip