#!/bin/bash


LANGUAGE="en"  
NAME="TEST" 
MODEL_TYPE="localpath/to/model"
PATH_TO_ADAPTER="../finetuning/finetune/output_history_plan_en/output__lora_history_plan_en"


nohup python -u test_set_inference_plan_model.py "$LANGUAGE" --name "$NAME" --model_type "$MODEL_TYPE" --path_to_adapter "$PATH_TO_ADAPTER" > eval_log_plan.txt &
