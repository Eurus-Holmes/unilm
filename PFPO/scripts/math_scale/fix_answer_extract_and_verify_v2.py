import json
import argparse
from glob import glob
import os
from tqdm import tqdm
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from data.mathscale.util import mathscale_is_equiv_proxy, is_correct as mathscale_is_correct, mathscale_extract_answer, mathscale_extract_answer_fn_v4
from data.math import number_answer_extractor
from post_processors.openai_api_callback import majority_voting_predict

"""
This file is used to fix the incorrect answer extraction and verification in the previous version of `mathscale_extract_answer_v2`.
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    if os.path.exists(args.input_file):
        data = json.load(open(args.input_file))
    else:
        data = []
        for file in glob(args.input_file):
            data += json.load(open(file))
        if len(data) == 0:
            raise ValueError(f"No data found in {args.input_file}")

    mathscale_fn = mathscale_extract_answer_fn_v4(completion_field="completion")
    data = mathscale_fn(data)

    cnt = 0
    pass_at_k = 0
    sc = 0
    inconsistent = 0
    missing = 0
    for item in data:
        if isinstance(item["label"], int):
            item["label"] = str(item["label"])

        res = []
        pred_clean = []
        for resp in item["response"]:
            tmp_res, tmp_pred_clean, _ = mathscale_is_correct(resp, item["label"])
            res.append(tmp_res)
            pred_clean.append(tmp_pred_clean)
        pred2res = {pred: r for pred, r in zip(pred_clean, res)}
        sc_pred = majority_voting_predict(pred_clean)
        sc_res = pred2res[sc_pred]

        tmp = 0
        for a, b in zip(pred_clean, item["pred"]):
            if a != b:
                tmp += 1
        inconsistent += tmp / len(pred_clean)

        item["pred"] = pred_clean
        item["res"] = res
        item["sc_pred"] = sc_pred
        item["sc_res"] = sc_res

        if res[0]:
            cnt += 1
        if any(res):
            pass_at_k += 1
        if item["sc_res"]:
            sc += 1

    print(inconsistent)
    print(missing)
    metrics = {"acc": cnt / len(data), "pass@k": pass_at_k / len(data), "maj@k": sc / len(data), "correct": cnt, "total": len(data)}
    print(metrics)
    json.dump(data, open(args.output_file, "w"), indent=2)
    json.dump(metrics, open(args.output_file.replace(".json", ".metrics.json"), "w"), indent=2)


if __name__ == '__main__':
    main()

"""
>>> 
"""
