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
        "leaf": ["knn_3", "nb_3", "rf_3", "knn_4", "nb_4", "rf_4", "knn_6", "nb_6", "rf_6", "knn_7", "nb_7", "rf_7"],
        "FeatureUnion": np.zeros(12),
        "NoneType": np.zeros(12),
        "PCA": np.zeros(12),
        "SelectKBest": np.zeros(12)
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

                    features_flag = pipeline["features"][0].split("_",1)[1]


                    #print(mf_data)
                    dataset_meta_features = mf_data[algorithm][(mf_data[algorithm]['ID'] == dataset)].iloc[0]
                    #print(dataset_meta_features)
                    if dataset_meta_features["ClassEntropy"] <= 0.863:
                        if dataset_meta_features["Quartile1MeansOfNumericAtts"] <= 9.329:
                            leaf = algorithm + "_3"
                        else:
                            leaf = algorithm + "_4"
                    else:
                        if dataset_meta_features["ClassEntropy"] <= 1.787:
                            leaf = algorithm + "_6"
                        else:
                            leaf = algorithm + "_7"
                    results_map.loc[results_map["leaf"] == leaf, features_flag] += 1
    print(count)
    results_map.to_csv(os.path.join(result_path, "rebalance_meta_learning_output_process.csv"), index=False)

    fig, axes = plt.subplots(nrows=1, ncols=1)
    results_map.plot(ax=axes, kind='bar', x='leaf')
    fig.savefig(os.path.join(result_path, "features_operator_meta_learning_output_process.pdf"), bbox_inches='tight')


main()