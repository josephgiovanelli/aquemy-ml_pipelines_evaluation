from __future__ import print_function
from os import listdir
from os.path import isfile, join

import os
import json
import itertools

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from utils import create_directory

def diff(first, second):
    second = set(second)
    return [item for item in first if item not in second]

def main():
    # configure environment
    input, result_path = "../results/summary/evaluation3", "../results/summary/evaluation3"
    input_auto = "../results/evaluation3/preprocessing_algorithm"
    result_path = create_directory(result_path, "extension")
    algorithms = ["knn", "nb", "rf"]

    ## Meta-features Loading
    all_classification = pd.read_csv('meta_features/extended_meta_features_all_classification.csv')
    openml_cc_18 = pd.read_csv('meta_features/extended_meta_features_openml_cc_18.csv')
    study_1 = pd.read_csv('meta_features/extended_meta_features_study_1.csv')
    all_classification = all_classification[all_classification['ID'].isin(diff(all_classification['ID'], openml_cc_18['ID']))]
    meta_features = pd.concat([openml_cc_18, all_classification, study_1], ignore_index=True, sort=True)
    
    ## Results Loading
    mf_data = {}
    for algorithm in algorithms:
        mf_data[algorithm] = pd.read_csv(os.path.join(input, algorithm + '.csv'))
        mf_data[algorithm].rename(columns={"dataset": "ID"}, inplace=True)

    ## Data Preparation
    for algorithm in algorithms:
        mf_data[algorithm] = pd.merge(mf_data[algorithm], meta_features, on="ID")

    results_map = pd.DataFrame({
        "leaf": ["other_1", "other_2", "other_3", "other_4", "union_1", "union_2", "union_3"],
        #"encode": np.zeros(4),
        "features": np.zeros(7),
        #"impute": np.zeros(4),
        "normalize": np.zeros(7),
        "discretize": np.zeros(7),
        "rebalance": np.zeros(7)
        })
    count = 0
    for algorithm in ["knn", "nb", "rf"]:

        df = pd.read_csv(os.path.join("..", "results", "summary", "evaluation3", algorithm + ".csv"))
        ids = list(df["dataset"])

        files = [f for f in listdir(input_auto) if isfile(join(input_auto, f))]
        results = [f[:-5] for f in files if f[-4:] == 'json']

        for dataset in ids:
            acronym = algorithm + "_" + str(dataset)
            if acronym in results:
                with open(os.path.join(input_auto, acronym + '.json')) as json_file:
                    data = json.load(json_file)
                    accuracy = data['context']['best_config']['score'] // 0.0001 / 100
                    pipeline = data['context']['best_config']['pipeline']

                    encode_flag = 1 if "None" not in pipeline["encode"][0] else 0
                    features_flag = 1 if "None" not in pipeline["features"][0] else 0
                    impute_flag = 1 if "None" not in pipeline["impute"][0] else 0
                    try:
                        normalize_flag = 1 if "None" not in pipeline["normalize"][0] else 0
                    except:
                        normalize_flag = 0
                    try:
                        discretize_flag = 1 if "None" not in pipeline["discretize"][0] else 0
                    except:
                        discretize_flag = 0
                    rebalance_flag = 1 if "None" not in pipeline["rebalance"][0] else 0

                    #print(mf_data)
                    dataset_meta_features = mf_data[algorithm][(mf_data[algorithm]['ID'] == dataset)].iloc[0]
                    #print(dataset_meta_features)
                    dataset_meta_features = mf_data[algorithm][(mf_data[algorithm]['ID'] == dataset)].iloc[0]
                    if dataset_meta_features["ClassEntropy"] <= 1.787:
                        if algorithm == "nb":
                            leaf = "union_1"
                        else:
                            if dataset_meta_features["AutoCorrelation"] > 0.701:
                                if dataset_meta_features["NumberOfFeatures"] <= 37:
                                    leaf = "union_2"
                                else:
                                    leaf = "other_2"
                            else:
                                if dataset_meta_features["Quartile1MeansOfNumericAtts"] > 0.934:
                                    if dataset_meta_features["PercentageOfNumericFeatures"] > 81.81:
                                        count += 1
                                        leaf = "union_3"
                                    else:
                                        leaf = "other_3"
                                else:
                                    leaf = "other_4"
                    else:
                        leaf = "other_1"
                    #results_map.loc[results_map["leaf"] == leaf, "encode"] = results_map.loc[results_map["leaf"] == leaf, "encode"] + encode_flag
                    results_map.loc[results_map["leaf"] == leaf, "features"] = results_map.loc[results_map["leaf"] == leaf, "features"] + features_flag
                    #results_map.loc[results_map["leaf"] == leaf, "impute"] = results_map.loc[results_map["leaf"] == leaf, "impute"] + impute_flag
                    results_map.loc[results_map["leaf"] == leaf, "normalize"] = results_map.loc[results_map["leaf"] == leaf, "normalize"] + normalize_flag
                    results_map.loc[results_map["leaf"] == leaf, "discretize"] = results_map.loc[results_map["leaf"] == leaf, "discretize"] + discretize_flag
                    results_map.loc[results_map["leaf"] == leaf, "rebalance"] = results_map.loc[results_map["leaf"] == leaf, "rebalance"] + rebalance_flag
    print(count)
    results_map.to_csv(os.path.join(result_path, "features_meta_learning_output_process.csv"), index=False)

    fig, axes = plt.subplots(nrows=1, ncols=1)
    results_map.plot(ax=axes, kind='bar', x='leaf')
    fig.savefig(os.path.join(result_path, "features_meta_learning_output_process.pdf"), bbox_inches='tight')


main()