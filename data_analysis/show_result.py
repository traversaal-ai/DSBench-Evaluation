
from tqdm import tqdm
import os
from datetime import datetime

# ========== CONFIGURATION ==========
# Set these to override auto-detection, or leave as None for interactive selection

MODEL = None  # Set to model name to override, e.g., "google/gemini-3-pro-preview"
TIMESTAMP = None  # Set to timestamp to override, e.g., "20260127_200036"

# If both are None, script will help you select interactively

DATA_JSON_PATH = "./data_subset_olive.json"
# DATA_JSON_PATH = "./data_sample.json"

# ===================================

def read_txt(path):
    with open(path, "r", encoding='utf-8') as f:
        return f.read()

def find_available_models(base_path: str):
    """Find all models that have evaluation runs"""
    if not os.path.exists(base_path):
        return []

    models = [d for d in os.listdir(base_path)
              if os.path.isdir(os.path.join(base_path, d))]
    return sorted(models)

def find_timestamps_for_model(base_path: str, model_name: str):
    """Find all timestamps for a given model"""
    model_folder = os.path.join(base_path, model_name)

    if not os.path.exists(model_folder):
        return []

    timestamps = [d for d in os.listdir(model_folder)
                  if os.path.isdir(os.path.join(model_folder, d))]

    # Get folder info
    timestamp_info = []
    for ts in timestamps:
        folder_path = os.path.join(model_folder, ts)

        # Check if results.json exists
        results_file = os.path.join(folder_path, "results.json")
        if not os.path.exists(results_file):
            continue

        mtime = os.path.getmtime(folder_path)
        timestamp_info.append({
            "timestamp": ts,
            "folder": folder_path,
            "modified": datetime.fromtimestamp(mtime)
        })

    # Sort by modification time (most recent first)
    timestamp_info.sort(key=lambda x: x["modified"], reverse=True)
    return timestamp_info

def select_model_and_timestamp(base_path: str):
    """Interactive selection of model and timestamp"""

    # Find available models
    models = find_available_models(base_path)

    if not models:
        raise ValueError(f"No evaluation runs found in {base_path}")

    print("\n" + "="*80)
    print("AVAILABLE MODELS")
    print("="*80)
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")
    print("="*80)

    # Select model
    while True:
        try:
            choice = input(f"\nSelect model (1-{len(models)}): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(models):
                selected_model = models[choice_num - 1]
                break
            else:
                print(f"Invalid choice. Please enter 1-{len(models)}")
        except ValueError:
            print(f"Invalid input. Please enter a number (1-{len(models)})")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            raise

    # Find timestamps for selected model
    timestamps = find_timestamps_for_model(base_path, selected_model)

    if not timestamps:
        raise ValueError(f"No evaluation runs found for model {selected_model}")

    print("\n" + "="*80)
    print(f"AVAILABLE RUNS FOR: {selected_model}")
    print("="*80)
    for i, ts_info in enumerate(timestamps, 1):
        print(f"{i}. {ts_info['timestamp']} (modified: {ts_info['modified'].strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*80)

    # Select timestamp
    while True:
        try:
            choice = input(f"\nSelect run (1-{len(timestamps)}) [default: 1 (most recent)]: ").strip()

            if choice == "":
                choice_num = 1
            else:
                choice_num = int(choice)

            if 1 <= choice_num <= len(timestamps):
                selected_timestamp = timestamps[choice_num - 1]["timestamp"]
                break
            else:
                print(f"Invalid choice. Please enter 1-{len(timestamps)}")
        except ValueError:
            print(f"Invalid input. Please enter a number (1-{len(timestamps)})")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            raise

    return selected_model, selected_timestamp

# ========== MODEL & TIMESTAMP SELECTION ==========

save_path = "./save_process"

if MODEL is None or TIMESTAMP is None:
    print("\n🔍 Auto-detecting evaluation runs...")
    selected_model, selected_timestamp = select_model_and_timestamp(save_path)

    # Use selected values
    if MODEL is None:
        model = selected_model
    else:
        model = MODEL
        # Need to sanitize and re-select timestamp
        sanitized_model = model.replace('/', '_').replace(':', '_')
        timestamps = find_timestamps_for_model(save_path, sanitized_model)
        if timestamps:
            selected_timestamp = timestamps[0]["timestamp"]  # Most recent
        else:
            raise ValueError(f"No evaluation runs found for model {model}")

    if TIMESTAMP is None:
        timestamp = selected_timestamp
    else:
        timestamp = TIMESTAMP

    print(f"\n✅ Selected:")
    print(f"   Model: {model}")
    print(f"   Timestamp: {timestamp}")
else:
    model = MODEL
    timestamp = TIMESTAMP
    print(f"\n✅ Using manually specified:")
    print(f"   Model: {model}")
    print(f"   Timestamp: {timestamp}")

# Sanitize model name for filesystem compatibility
sanitized_model = model.replace('/', '_').replace(':', '_')

# Build paths
result_dir = os.path.join(save_path, sanitized_model, timestamp)

# Verify the directory exists
if not os.path.exists(result_dir):
    raise ValueError(f"Evaluation directory not found: {result_dir}")

print(f"\n📁 Reading from: {result_dir}")
print("="*80 + "\n")

# Load samples
samples = []
with open(DATA_JSON_PATH, "r") as f:
    for line in f:
        samples.append(eval(line.strip()))


results = []
with open(os.path.join(result_dir, "results.json"), "r") as f:
    for line in f:
        results += eval(line.strip())

costs = []
time_cost = []

# Track skipped samples
skipped_samples = []

id = 0
for sample in tqdm(samples):
    result = []
    if len(sample["questions"]) > 0:
        # Check if sample file exists
        sample_file_path = os.path.join(result_dir, sample['id']+".json")

        if not os.path.exists(sample_file_path):
            # Sample file not found - skip this sample
            skipped_samples.append(sample['id'])
            print(f"\n⚠️  Warning: Sample file not found: {sample['id']}.json")
            print(f"   This sample is in DATA_JSON but was not evaluated. Skipping...")
            continue

        try:
            # Read all predictions and deduplicate by question_idx
            predicts_by_idx = {}  # question_idx -> entry

            with open(sample_file_path, "r") as f:
                for line in f:
                    pre = eval(line.strip())
                    # Only keep successful entries, overwrite if duplicate question_idx
                    if 'error' not in pre:
                        predicts_by_idx[pre['question_idx']] = pre

            # Extract costs from deduplicated entries in order
            for idx in range(len(sample["questions"])):
                if idx in predicts_by_idx:
                    costs.append(predicts_by_idx[idx].get('cost', 0))
                    time_cost.append(predicts_by_idx[idx].get('time', 0))

        except Exception as e:
            # Catch any other unexpected errors during processing
            print(f"\n❌ Error processing sample {sample['id']}: {e}")
            print(f"   Skipping this sample and continuing...")
            skipped_samples.append(sample['id'])
            continue

    id += 1




results_c = []
for i, result in enumerate(results):
    if "true" in result.lower():
        results_c.append(True)
    else:
        results_c.append(False)
    # if i>=11:
    #     break

idx = 0
score4cha = []

for i, sample in enumerate(samples):
    if len(sample["questions"]) > 0:
        score_ = sum(results_c[idx:idx+len(sample["questions"])]) / len(sample["questions"])
        idx += len(sample["questions"])
        score4cha.append(score_)

# Calculate metrics
acc = sum(results_c) / len(results_c)
avg_challenge_acc = sum(score4cha) / len(score4cha)
total_cost = sum(costs)
total_time = sum(time_cost)

# Format output
output_lines = [
    f"Model Used: {model}",
    f"Timestamp: {timestamp}",
    f"Total Questions: {len(results_c)}",
    f"Total Challenges: {len(score4cha)}",
    f"Total Inference Time: {total_time:.2f} seconds",
    f"Total Cost: $ {total_cost:.2f}",
    f"Task Level Accuracy: {acc * 100:.2f} %",
    f"Competition Level Accuracy: {avg_challenge_acc * 100:.2f} %",
]

# Print to console
print()
print("="*60)
for line in output_lines:
    print(line)
print("="*60)
print()
print(f"Accuracy for each challenge: {score4cha}")

# Save to file
output_file = os.path.join(result_dir, "evaluation_summary.txt")
with open(output_file, "w", encoding='utf-8') as f:
    f.write("="*60 + "\n")
    f.write("EVALUATION SUMMARY\n")
    f.write("="*60 + "\n\n")
    for line in output_lines:
        f.write(line + "\n")
    f.write("\n" + "="*60 + "\n")
    f.write(f"\nAccuracy for each challenge: {score4cha}\n")
    f.write(f"Average accuracy for {len(score4cha)} challenges: {avg_challenge_acc * 100:.2f} %\n")

print(f"\n✅ Summary saved to: {output_file}")
