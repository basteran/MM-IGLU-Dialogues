import json
import csv
import argparse
from sklearn.metrics.pairwise import cosine_similarity
import re
from sentence_transformers import SentenceTransformer, util

# Load the sentence encoder model
model = SentenceTransformer('all-MiniLM-L6-v2')

def process_string(input_string):
    """Post-processing the generated output, if needed"""
    
    
    lines = input_string.split('\n')
    
    if len(lines) > 1:
        return lines[1].strip(' "')
    else:
        return lines[0].strip(' "')
    
def semantic_similarity(sentence1, sentence2):
    """Compute cosine similarity between two sentences"""
    embeddings = model.encode([sentence1, sentence2], convert_to_tensor=True)
    similarity = util.cos_sim(embeddings[0], embeddings[1])
    return similarity.item()


def extract_example_ids(json_file_path, tsv_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    example_ids = []
    for entry in data:
        for convo in entry.get("conversations", []):
            if convo["role"] == "plan" and convo["content"] == "['CONFIRMATION WITH RECAP']":
                if 'noplan' in tsv_file_path or 'ZS' in tsv_file_path:
                    example_id = re.sub(r'_(plan|question)$', '', entry["example_id"])
                else:
                    example_id = entry["example_id"]
                example_ids.append(example_id)
                break  
    return example_ids

def calculate_metrics(tsv_file_path, example_ids, threshold):
    total_similarity = 0
    count_above_threshold = 0
    total_examples = 0
    
    with open(tsv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        
        for row in reader:
            example_id = row['example_id']
            if example_id in example_ids:
                expected = row['expected_output']
                predicted = process_string(row['predicted_output'])
                print(expected)
                print(predicted)
                print('------------------------------------')
                
                similarity = semantic_similarity(expected, predicted)
                total_similarity += similarity
                total_examples += 1
                
                if similarity > threshold:
                    count_above_threshold += 1
    
    if total_examples == 0:
        raise ValueError("No example_id found in the .tsv file corresponding to the extracted IDs.")
    
    print("Number of examples with CONFIRMATION WITH RECAP: "+str(total_examples))
    print("Number of examples above the threshold: "+str(count_above_threshold))
    average_similarity = total_similarity / total_examples
    semantic_accuracy = count_above_threshold / total_examples
    return average_similarity, semantic_accuracy


def main():
    parser = argparse.ArgumentParser(description="Extract example IDs and calculate similarity metrics from a TSV file")
    parser.add_argument("tsv_file", type=str, help="Path to the TSV file")
    
    args = parser.parse_args()
    
    json_file_path = "../data/en/history_plan/dialogues_ENG_test_multitask.json"  # Reference file
    
    # Extract example_id that contain "CONFIRMATION WITH RECAP"
    example_ids = extract_example_ids(json_file_path, args.tsv_file)
    print(f"Extracted examples: {example_ids}")
    
    threshold = 0.92
    average_similarity, semantic_accuracy = calculate_metrics(args.tsv_file, example_ids, threshold)
    
    print(f"AVG Cosine Similarity: {average_similarity:.4f}")
    print(f"Examples with Cosine Similarity above threshold {threshold}: {semantic_accuracy:.4f}")

if __name__ == "__main__":
    main()