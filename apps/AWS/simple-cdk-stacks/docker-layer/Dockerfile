FROM public.ecr.aws/lambda/python:3.10

# Install any system dependencies
RUN yum install -y your-system-dependencies

# Copy requirements.txt if you have one
COPY requirements.txt .
RUN pip install -r requirements.txt -t /opt/python/lib/python3.10/site-packages/

# Copy any additional files needed
COPY ./python/ /opt/