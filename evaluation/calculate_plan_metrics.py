import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
import re
import argparse




def process_plan_string(input_string):
    """Post-processing the generated output, if needed"""
    if pd.isna(input_string):
            input_string = "['']"
    
    lines = input_string.split('\n')
    
    
    if len(lines) > 1:
        return lines[1].strip(' "')
    else:
        
        return lines[0].strip(' "')

def adjust_values(input_string):
    """Post-processing the generated output, if needed"""
    items = input_string.strip("[]").split(", ")
    
    result = [f"'{item.strip()}'" for item in items]
    return f"[{', '.join(result)}]"

def calculate_metrics(data):
    all_gold = []
    all_pred = []
    
    unique_labels = set()  
    
   
    i = 0
    for _, row in data.iterrows():
        gold = row['expected_output']
        pred = row['predicted_output']
        #print(pred)
        pred = process_plan_string(pred)
        
        
        match = re.search(r'\[.*?\]', pred)
        pred = match.group(0) if match else "['']"
        #print(pred) 
        
        
        if "'" not in pred:
            pred = adjust_values(pred)

        if isinstance(gold, str):
            gold = eval(gold)
        if isinstance(pred, str):
            pred = eval(pred)
        i +=1
        print(f"{i} Expected: {gold}")
        print(f"{i} Predicted: {pred}")
        

        unique_labels.update(gold)
        unique_labels.update(pred)
        all_gold.append(set(gold))
        all_pred.append(set(pred))
    
    unique_labels = list(unique_labels)
    #print(len(all_gold))
    #print(len(all_pred))
    
    y_true = []
    y_pred = []
    
    for gold, pred in zip(all_gold, all_pred):
        y_true.append([1 if label in gold else 0 for label in unique_labels])
        y_pred.append([1 if label in pred else 0 for label in unique_labels])
    
    
    example_precisions = []
    example_recalls = []
    example_f1s = []
    
    for gold, pred in zip(all_gold, all_pred):
        tp = len(gold & pred)  # True positives
        fp = len(pred - gold)  # False positives
        fn = len(gold - pred)  # False negatives
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        example_precisions.append(precision)
        example_recalls.append(recall)
        example_f1s.append(f1)
    
    # Compute mean example based metrics
    precision = sum(example_precisions) / len(example_precisions)
    recall = sum(example_recalls) / len(example_recalls)
    f1 = sum(example_f1s) / len(example_f1s)
    
    # Compute micro/macro metrics
    precision_micro = precision_score(y_true, y_pred, average='micro')
    recall_micro = recall_score(y_true, y_pred, average='micro')
    f1_micro = f1_score(y_true, y_pred, average='micro')
    
    precision_macro = precision_score(y_true, y_pred, average='macro')
    recall_macro = recall_score(y_true, y_pred, average='macro')
    f1_macro = f1_score(y_true, y_pred, average='macro')
    
    # Accuracy
    exact_match_count = sum([pred == gold for gold, pred in zip(all_gold, all_pred)])
    accuracy = exact_match_count / len(data)
    #print(exact_match_count)
    #print(len(data))
    
    return {
        "accuracy": accuracy,
        "EXAMPLE_precision": precision,
        "EXAMPLE_recall": recall,
        "EXAMPLE_f1": f1,
        "precision_micro": precision_micro,
        "recall_micro": recall_micro,
        "f1_micro": f1_micro,
        "precision_macro": precision_macro,
        "recall_macro": recall_macro,
        "f1_macro": f1_macro
    }



def main():
    parser = argparse.ArgumentParser(description="Calculate precision, recall, and F1 score from a TSV file.")
    parser.add_argument("tsv_file", type=str, help="Path to the TSV file")
    args = parser.parse_args()
    
    data = pd.read_csv(args.tsv_file, sep='\t')
    metrics = calculate_metrics(data)
    
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

if __name__ == "__main__":
    main()