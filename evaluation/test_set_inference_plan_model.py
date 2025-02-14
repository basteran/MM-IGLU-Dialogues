import json
import csv
import argparse
from peft import PeftModel
from transformers import AutoModel, AutoTokenizer
from PIL import Image
import torch
import re
from SystemPrompt import get_system_prompt




def parse_json_to_msgs(input_json):
    """
    Convert each instance of the JSON into the format required by the model for generation, including the example_id.
    Split the conversations into "messages_input" and "messages_output".

    Args:

        input_json (list): A list of dictionaries containing the conversations.
        Returns:

        list: A list of instances converted into the required format.
    """
    results = []

    for instance in input_json:
        msgs = []
        image = instance.get("image", "")
        example_id = instance.get("example_id", "")
        conversations = instance.get("conversations", [])

        for conversation in conversations:
            role = conversation.get("role", "")
            content = conversation.get("content", "")

            if role == "user" and "<image>" in content:
                # Split image and text
                image_content = content.split("\n", 1)
                if len(image_content) == 2:
                    image_placeholder, user_content = image_content
                else:
                    user_content = image_content[0]
                msgs.append({"role": "user", "content": [image, user_content]})
            else:
                msgs.append({"role": role, "content": content})

        # Split conversations in inputand output
        messages_input = msgs[:-1]  # All dialogue turns except the last one
        messages_output = msgs[-1:]  # The last turn of the dialogue

        # Add example_id as metadata
        results.append({
            "example_id": example_id,
            "messages_input": messages_input,
            "messages_output": messages_output
        })
    #print(results[2]["messages_input"])
    return results

def generate(messages_input, example_id, lang, lora_model, tokenizer):

    """
    Generate a string for k turn in a conversation (a question or a plan) given the k-1 turns of the conversations in input
    It prepend the specific system prompt based on the task (question generation or plan generation )
    Args:

        messages_input: A dictionary containing a conversations
        example_id
        Returns:

        string: The model generated string
    """
    if 'question' in example_id:
        sys_prompt = get_system_prompt('question', lang)
        output_type = 'assistant'
    elif 'plan':
        sys_prompt = get_system_prompt('plan', lang)
        output_type = 'plan'

    print(sys_prompt)

    image_path = messages_input[0]["content"][0]
    image = Image.open(image_path.replace("../../images/", "../data/images/")).convert('RGB')
    messages_input[0]["content"][0] = image
    print(messages_input[0]["content"][0])

    
    res = lora_model.chat(
        image=None,
        msgs=messages_input,
        tokenizer=tokenizer,
        output_type = output_type,
        system_prompt = sys_prompt,
        
        sampling = False,
        
    )
    
    return res
    
    
    
    

def write_tsv_files(results, question_file, plan_file, lang, lora_model, tokenizer):
    """
    Writes two separate TSV files for instances of the "question generation" or "plan generation" task.
    Args:  
        results (list): List of processed instances.  
        question_file (str): Path to the TSV file for instances with "question".  
        plan_file (str): Path to the TSV file for instances with "plan".    

    """
    question_rows = []
    plan_rows = []

    for instance in results:
        example_id = instance["example_id"]
        messages_input = instance["messages_input"]
        messages_output = instance["messages_output"]

        # Extracted expected output
        expected_output = messages_output[0]["content"] if messages_output else ""
        # Compute the predicted_output
        predicted_output = generate(messages_input, example_id, lang, lora_model, tokenizer)

        row = {
            "example_id": example_id,
            "expected_output": expected_output,
            "predicted_output": predicted_output
        }
        print("---------------------------------------------------------------")
        print(messages_input)
        print(f"example id: {example_id}")
        print(f"expected: {expected_output}")
        print(f"predicted: {predicted_output}")
        print("---------------------------------------------------------------")

        if "question" in example_id:
            question_rows.append(row)
        elif "plan" in example_id:
            plan_rows.append(row)

    # Write the TSV
    with open(question_file, "w", newline="", encoding = 'utf-8') as qf:
        writer = csv.DictWriter(qf, fieldnames=["example_id", "expected_output", "predicted_output"], delimiter="\t")
        writer.writeheader()
        writer.writerows(question_rows)

    with open(plan_file, "w", newline="", encoding = 'utf-8') as pf:
        writer = csv.DictWriter(pf, fieldnames=["example_id", "expected_output", "predicted_output"], delimiter="\t")
        writer.writeheader()
        writer.writerows(plan_rows)

# load the JSON
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("language", choices=["en", "it","en2it","it2en"], help="Language configuration(either 'en','it','en2it' or 'it2en')")
    parser.add_argument("--model_type", type=str, default="openbmb/MiniCPM-V-2_6", help="Base model")
    parser.add_argument("--path_to_adapter", type=str, default="../finetuning/finetune/output_history_plan_en/output__lora_history_plan_en", help="Path to the fine-tuned LoRA adapter")
    parser.add_argument("--name", default="TEST", help="Custom name for the output TSV files")
    
    args = parser.parse_args()

    if args.language == 'en' or args.language == 'it2en': 
        input_file = "../data/en/history_plan/dialogues_ENG_test_multitask.json"
    else:
        input_file = "../data/it/history_plan/dialogues_test_multitask.json"


    question_tsv = f"{args.language.upper()}_{args.name}_generated_questions.tsv"
    plan_tsv = f"{args.language.upper()}_{args.name}_generated_plans.tsv"

    model = AutoModel.from_pretrained(
        args.model_type,
        trust_remote_code=True,
        attn_implementation='sdpa',
        torch_dtype=torch.bfloat16
    )

    lora_model = PeftModel.from_pretrained(
        model,
        args.path_to_adapter,
        device_map="auto",
        trust_remote_code=True
    ).eval().cuda()

    tokenizer = AutoTokenizer.from_pretrained(args.model_type, trust_remote_code=True)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    formatted_msgs = parse_json_to_msgs(data)
    write_tsv_files(formatted_msgs, question_tsv, plan_tsv, args.language, lora_model, tokenizer)

    print(f"TSV files saved: {question_tsv}, {plan_tsv}")
    
if __name__ == "__main__":
    main()
