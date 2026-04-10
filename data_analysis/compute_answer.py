import json

from tqdm import tqdm
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# ========== CONFIGURATION ==========
# Set these to override auto-detection, or leave as None for interactive selection

MODEL = None  # Set to model name to override, e.g., "google/gemini-3-pro-preview"
TIMESTAMP = None  # Set to timestamp to override, e.g., "20260127_200036"

# If both are None, script will help you select interactively

DATA_JSON_PATH = "./data_subset_olive.json"
# DATA_JSON_PATH = "./data_sample.json"

# ===================================

client = OpenAI()

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

    # Get folder info with sample file counts
    timestamp_info = []
    for ts in timestamps:
        folder_path = os.path.join(model_folder, ts)

        # Count sample JSON files (exclude results.json and results_process.json)
        json_files = [f for f in os.listdir(folder_path)
                     if f.endswith('.json')
                     and f not in ['results.json', 'results_process.json']]

        # Check if results.json already exists
        results_exists = os.path.exists(os.path.join(folder_path, "results.json"))

        mtime = os.path.getmtime(folder_path)
        timestamp_info.append({
            "timestamp": ts,
            "folder": folder_path,
            "modified": datetime.fromtimestamp(mtime),
            "samples": len(json_files),
            "results_exists": results_exists
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
        status = "✅ Already evaluated" if ts_info['results_exists'] else "⚠️  Not yet evaluated"
        print(f"{i}. {ts_info['timestamp']} - {ts_info['samples']} samples ({status})")
        print(f"   Modified: {ts_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
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
                selected_ts_info = timestamps[choice_num - 1]

                # Warn if already evaluated
                if selected_ts_info['results_exists']:
                    print(f"\n⚠️  Warning: This run already has results.json")
                    confirm = input("This will overwrite existing results. Continue? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("Cancelled.")
                        raise KeyboardInterrupt

                selected_timestamp = selected_ts_info["timestamp"]
                break
            else:
                print(f"Invalid choice. Please enter 1-{len(timestamps)}")
        except ValueError:
            print(f"Invalid input. Please enter a number (1-{len(timestamps)})")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            raise

    return selected_model, selected_timestamp

# Load samples first (needed for validation)
samples = []
with open(DATA_JSON_PATH, "r") as f:
    for line in f:
        samples.append(eval(line.strip()))


def evaluate_prediction(client, question, answer, prediction):
    prompt = (f"Please judge whether the generated answer is right or wrong. We require that the correct answer "
              f"to the prediction gives a clear answer, not just a calculation process or a disassembly of ideas. "
              f"The question is {question}. The true answer is \n {answer}. \n The predicted answer is \n {prediction}.\n "
              f"If the predicted answer is right, please output True. Otherwise output Flase. "
              f"Don't output any other text content. You only can output True or False.")
    response = client.chat.completions.create(
      model="gpt-4o-2024-05-13",
    #   model="gpt-5-mini-2025-08-07"
      messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": prompt
            }
          ]
        }
      ],
      temperature=0,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    # print(prompt)
    # print(response.choices[0].message.content)
    # exit()
    return response.choices[0].message.content

def read_txt(path):
    with open(path, "r", encoding='utf-8') as f:
        return f.read()

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

results = []

# Create nested directory structure
result_dir = os.path.join(save_path, sanitized_model, timestamp)

# Verify the directory exists and has sample files
if not os.path.exists(result_dir):
    raise ValueError(f"Evaluation directory not found: {result_dir}")

sample_files = [f for f in os.listdir(result_dir)
                if f.endswith('.json')
                and f not in ['results.json', 'results_process.json']]

if not sample_files:
    raise ValueError(f"No sample files found in {result_dir}. Run evaluation first.")

print(f"\n📁 Evaluating predictions from: {result_dir}")
print(f"📊 Found {len(sample_files)} sample files to evaluate")
print("="*80 + "\n")

save_f = open(os.path.join(result_dir, "results.json"), "w")
save_process = open(os.path.join(result_dir, "results_process.json"), "w")

# Track skipped samples
skipped_samples = []
processed_samples = []

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
            # Read predictions from file
            predicts = []
            with open(sample_file_path, "r") as f:
                for line in f:
                    predicts.append(eval(line.strip()))

            # Safety check: ensure we have enough predictions
            num_questions = len(sample["questions"])
            num_predictions = len(predicts)

            if num_predictions < num_questions:
                print(f"\n⚠️  Warning: Sample {sample['id']} has {num_questions} questions but only {num_predictions} predictions")
                print(f"   Treating {num_questions - num_predictions} missing predictions as incorrect")
                # Pad with error entries
                for i in range(num_questions - num_predictions):
                    predicts.append({'error': 'Missing prediction - evaluation incomplete'})

            questions = []
            for id, question_name in enumerate(tqdm(sample["questions"])):
                question = read_txt(os.path.join("./data", sample["id"], question_name + ".txt"))
                pre = predicts[id]

                try:
                    # Check if prediction failed
                    if 'error' in pre:
                        print(f"Prediction failed for {sample['id']}, question {id}: {pre['error']}")
                        ans = "False"
                        process = [sample["id"], ans, str(sample["answers"][id]), f"ERROR: {pre['error']}"]
                    elif not model.endswith('autoagent'):
                        ans = evaluate_prediction(client, question, str(sample["answers"][id]), pre['response'])
                        process = [sample["id"], ans, str(sample["answers"][id]), pre['response'][:]]
                    else:
                        ans = evaluate_prediction(client, question, str(sample["answers"][id]), pre['summary'])
                        process = [sample["id"], ans, str(sample["answers"][id]), pre['summary'][:]]
                except KeyError as e:
                    print(f"Missing key {e} in prediction for {sample['id']}, question {id}")
                    print(f"Available keys: {pre.keys()}")
                    ans = "False"
                    process = [sample["id"], ans, str(sample["answers"][id]), "ERROR: Missing response"]
                except Exception as e:
                    print(e)
                    ans = "False"
                    process = [sample["id"], ans, str(sample["answers"][id]), f"ERROR: {str(e)}"]

                result.append(ans)
                json.dump(process, save_process)
                save_process.write("\n")
                save_process.flush()

            processed_samples.append(sample['id'])

        except Exception as e:
            # Catch any other unexpected errors during processing
            print(f"\n❌ Error processing sample {sample['id']}: {e}")
            print(f"   Skipping this sample and continuing...")
            skipped_samples.append(sample['id'])
            continue

    json.dump(result, save_f)
    save_f.write("\n")
    save_f.flush()
    results += result

save_f.close()
save_process.close()

# Print summary of processing
print("\n" + "="*80)
print("PROCESSING SUMMARY")
print("="*80)
print(f"Total samples in DATA_JSON: {len(samples)}")
print(f"Samples processed: {len(processed_samples)}")
print(f"Samples skipped: {len(skipped_samples)}")

if skipped_samples:
    print(f"\n⚠️  Skipped samples (not found in evaluation directory):")
    for sample_id in skipped_samples:
        print(f"   - {sample_id}")
    print(f"\n💡 These samples are in your DATA_JSON file but were not evaluated.")
    print(f"   If you want to include them, run the evaluation notebook for these samples.")

print("="*80 + "\n")

results_c = []
for i, result in enumerate(results):
    if "true" in result.lower():
        results_c.append(True)
    else:
        results_c.append(False)

idx = 0
score4cha = []
for sample in tqdm(samples):
    if len(sample["questions"]) > 0:
        # Only process samples that were actually evaluated
        if sample['id'] not in skipped_samples:
            score_ = sum(results_c[idx:idx+len(sample["questions"])]) / len(sample["questions"])
            idx += len(sample["questions"])
            score4cha.append(score_)

print(f"\nAccuracy for each challenge is {score4cha}")

if len(results_c) > 0:
    acc = sum(results_c) / len(results_c)
    print(f"Accuracy for all the {len(results_c)} questions is {acc}")
else:
    print("⚠️  No results to evaluate. All samples were skipped.")