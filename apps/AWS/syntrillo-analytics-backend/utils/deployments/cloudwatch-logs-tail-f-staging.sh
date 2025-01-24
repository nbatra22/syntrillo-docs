#!/bin/bash

aws logs --profile syntrillo-clinic-staging tail /aws/lambda/IFrameGeneratorFunction --follow 
