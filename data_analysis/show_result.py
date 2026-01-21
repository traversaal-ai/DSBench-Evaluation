
from tqdm import tqdm
import os


samples = []
with open("./data_subset_olive.json", "r") as f:
    for line in f:
        samples.append(eval(line.strip()))

def read_txt(path):
    with open(path, "r", encoding='utf-8') as f:
        return f.read()

save_path = "./save_process"
# model = 'llava-v1.5-13b'
# model = 'llama-3-8b-instruct'
# model = "gpt-3.5-turbo-0125"
# model = "gpt-4-turbo-2024-04-09"
# model = 'gpt-4o-2024-05-13'
# model = "gpt-5-mini-2025-08-07"
model = "gpt-5-nano-2025-08-07"


results = []
with open(os.path.join(save_path, model, "results.json"), "r") as f:
    for line in f:
        results += eval(line.strip())

costs = []
time_cost = []

id = 0
for sample in tqdm(samples):
    result = []
    if len(sample["questions"]) > 0:
        predicts = []
        with open(os.path.join(save_path, model, sample['id']+".json"), "r") as f:
            for line in f:
                pre = eval(line.strip())
                predicts.append(pre)
                costs.append(pre['cost'])
                time_cost.append(pre['time'])
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

acc = sum(results_c) / len(results_c)
print(f"Accuracy for all the {len(results_c)} questions is {acc}")
print(f"Cost for all the {len(results_c)} questions is {sum(costs)}")
print(f"Consume time for all the {len(results_c)} questions is {sum(time_cost)}")
print()


print(f"Accuracy for each challenge is {score4cha}")
print(f"Average accuracy for {len(score4cha)} challenge is {sum(score4cha)/len(score4cha)}")
