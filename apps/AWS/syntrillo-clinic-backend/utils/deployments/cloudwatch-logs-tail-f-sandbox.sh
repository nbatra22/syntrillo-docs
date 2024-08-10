#!/bin/bash

aws logs --profile syntrillo-clinic-sandbox tail /aws/lambda/IFrameGeneratorFunction --follow 
