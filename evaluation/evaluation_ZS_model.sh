#!/bin/bash



LANGUAGE="en"
NAME="TEST"
MODEL_TYPE="localpath/to/model"

nohup python -u test_set_inference_ZS_model.py "$LANGUAGE" --name "$NAME" --model_type "$MODEL_TYPE" > eval_log_ZS.txt &
