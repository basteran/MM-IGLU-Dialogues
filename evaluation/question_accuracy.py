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




def calculate_metrics(tsv_file_path, threshold):
    total_similarity = 0
    count_above_threshold = 0
    exact_match_count = 0
    total_examples = 0

    with open(tsv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')

        for row in reader:
            
        
            expected = row['expected_output']
            predicted = process_string(row['predicted_output'])
            print(expected)
            print(predicted)
            print('------------------------------------')
            

            similarity = semantic_similarity(expected, predicted)
            total_similarity += similarity

            if similarity > threshold:
                count_above_threshold += 1

            if expected == predicted:
                exact_match_count += 1

            total_examples += 1

    if total_examples == 0:
        raise ValueError("No example found in the .tsv file")

    print("TOTAL EXAMPLES: " + str(total_examples))
    print("TOTAL EXAMPLES ABOVE THRESHOLD: " + str(count_above_threshold))
    print("TOTAL EXACT MATCH: " + str(exact_match_count))

    
    average_similarity = total_similarity / total_examples
    semantic_accuracy = count_above_threshold / total_examples
    exact_match_accuracy = exact_match_count / total_examples

    return average_similarity, semantic_accuracy, exact_match_accuracy



def main():
    parser = argparse.ArgumentParser(description="Calculate metrics from a TSV file")
    parser.add_argument("tsv_file", type=str, help="Path to the TSV file")
    threshold = 0.92
    args = parser.parse_args()
    
    average_similarity, semantic_accuracy, exact_match_accuracy = calculate_metrics(args.tsv_file, threshold)
    
    print("---------METRICS-------------")
    print(f"AVG Cosine Similarity: {average_similarity:.4f}")
    print(f"Examples with Cosine Similarity above threshold {threshold}: {semantic_accuracy:.4f}")
    print(f"Base Accuracy (exact matches): {exact_match_accuracy:.4f}")
    print("----------------------------------------------")

if __name__ == "__main__":
    main()

