#!/bin/bash

LANGUAGE="en"  
NAME="TEST"
MODEL_TYPE="localpath/to/model"
PATH_TO_ADAPTER="../finetuning/finetune/output_history_noplan_en/output__lora_history_noplan_en"


nohup python -u test_set_inference_noplan_model.py "$LANGUAGE" --name "$NAME" --model_type "$MODEL_TYPE" --path_to_adapter "$PATH_TO_ADAPTER" > eval_log_noplan.txt &
