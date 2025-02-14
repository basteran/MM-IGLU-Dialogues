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

        if 'plan' in example_id:
            continue

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
    return results

def generate(messages_input, lang, model, tokenizer):

    """
    Generate a string for k turn in a conversation (a question or a plan) given the k-1 turns of the conversations in input
    It prepend the specific system prompt based on the task (question generation or plan generation )
    Args:

        messages_input: A dictionary containing a conversations
        
        Returns:

        string: The model generated string
    """
    
    sys_prompt = get_system_prompt('other', lang)
    print(sys_prompt)

    image_path = messages_input[0]["content"][0]
    image = Image.open(image_path.replace("../../images/", "../data/images/")).convert('RGB')
    messages_input[0]["content"][0] = image
    print(messages_input[0]["content"][0])

    
    res = model.chat(
        image=None,
        msgs=messages_input,
        tokenizer=tokenizer,
        output_type = 'assistant',
        system_prompt = sys_prompt,
        
        sampling = False,
        
    )
    
    
    return res


def write_tsv_files(results, question_file, lang, model, tokenizer):
    
    question_rows = []
   

    for instance in results:
        example_id = instance["example_id"]
        messages_input = instance["messages_input"]
        messages_output = instance["messages_output"]

        # Extracted expected output
        expected_output = messages_output[0]["content"] if messages_output else ""
        # Compute the predicted_output
        predicted_output = generate(messages_input, lang, model, tokenizer)
        print("---------------------------------------------------------------")
        print(messages_input)
        print(f"example id: {example_id}")
        print(f"expected: {expected_output}")
        print(f"predicted: {predicted_output}")
        print("---------------------------------------------------------------")

        row = {
            "example_id": example_id,
            "expected_output": expected_output,
            "predicted_output": predicted_output
        }

        
        question_rows.append(row)
        

    # Write the TSV
    with open(question_file, "w", newline="", encoding = 'utf-8') as qf:
        writer = csv.DictWriter(qf, fieldnames=["example_id", "expected_output", "predicted_output"], delimiter="\t")
        writer.writeheader()
        writer.writerows(question_rows)

    

# load the JSON
def main():
    
    parser = argparse.ArgumentParser(description="Process test set JSON file and output a TSV with the triple (example id,expexted output, generated output")
    parser.add_argument("language", choices=["en", "it"], help="Language configuration(either 'en' or 'it')")
    parser.add_argument("--model_type", default="openbmb/MiniCPM-V-2_6", help="Base model")
    parser.add_argument("--name", default="TEST", help="Custom name for the output TSV file")

    args = parser.parse_args()

    input_file = f"../data/{args.language}/history_noplan/dialogues_{'eng' if args.language == 'en' else 'ita'}_test_question_history_noplan.json"
    question_tsv = f"{args.language.upper()}_{args.name}_generated_questions_ZS.tsv"

    # Load the original model
    
    model =  AutoModel.from_pretrained(
            args.model_type,
            trust_remote_code=True,
            attn_implementation='sdpa',
            torch_dtype=torch.bfloat16
            )

    model = model.eval().cuda()

    tokenizer = AutoTokenizer.from_pretrained(args.model_type, trust_remote_code=True)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    
    formatted_msgs = parse_json_to_msgs(data)

    # Write results in TSV file
    write_tsv_files(formatted_msgs, question_tsv, args.language, model, tokenizer)

    print(f"TSV file saved: {question_tsv} (Language: {args.language})")
if __name__ == "__main__":
    main()
