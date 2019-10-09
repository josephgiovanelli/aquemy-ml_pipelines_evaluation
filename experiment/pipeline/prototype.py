from imblearn.under_sampling import NearMiss, CondensedNearestNeighbour
from imblearn.over_sampling import SMOTE
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest
from sklearn.impute import SimpleImputer
from sklearn.impute._iterative import IterativeImputer
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import RobustScaler, StandardScaler, MinMaxScaler, PowerTransformer, KBinsDiscretizer, \
    Binarizer, OneHotEncoder, OrdinalEncoder, FunctionTransformer

from imblearn.pipeline import Pipeline

from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest
from sklearn.pipeline import FeatureUnion

from experiment.pipeline.PrototypeSingleton import PrototypeSingleton


def get_baseline():
    baseline = {}
    for k in PrototypeSingleton.getInstance().getPrototype().keys():
        baseline[k] = ('{}_NoneType'.format(k), {})
    return baseline

def pipeline_conf_to_full_pipeline(args, algorithm, seed, algo_config):
        if args == {}:
            args = get_baseline()
        op_to_class = {'pca': PCA, 'selectkbest': SelectKBest}
        operators = []
        for part in PrototypeSingleton.getInstance().getParts():
            item = args[part]
            if 'NoneType' in item[0]:
                continue
            else:
                params =  {k.split('__', 1)[-1]:v for k,v in item[1].items()}
                if item[0] == 'features_FeatureUnion':
                    fparams = {'pca':{}, 'selectkbest':{}}
                    for p,v in params.items():
                        op = p.split('__')[0]
                        pa = p.split('__')[1]
                        if op not in fparams:
                            fparams[op] = {}
                        fparams[op][pa] = v
                    oparams = []
                    for p,v in fparams.items():
                        oparams.append((p, op_to_class[p](**v)))
                    operator = FeatureUnion(oparams)
                    operators.append((part, operator))
                elif item[0].split('_',1)[0] == 'encode':
                    numerical_features, categorical_features = PrototypeSingleton.getInstance().getFeatures()
                    operator = ColumnTransformer(
                        transformers=[
                            ('num', Pipeline(steps=[('identity_numerical', FunctionTransformer())]),
                             numerical_features),
                            ('cat', Pipeline(steps=[('encoding', globals()[item[0].split('_', 1)[-1]](**params))]),
                             categorical_features)])
                    operators.append((part, operator))
                elif item[0].split('_', 1)[0] == 'normalizer':
                    numerical_features, categorical_features = PrototypeSingleton.getInstance().getFeatures()
                    operator = ColumnTransformer(
                        transformers=[
                            ('num', Pipeline(steps=[('normalizing', globals()[item[0].split('_', 1)[-1]](**params))]),
                             numerical_features),
                            ('cat', Pipeline(steps=[('identity_categorical', FunctionTransformer())]),
                             categorical_features)])
                    operators.append((part, operator))
                elif item[0].split('_', 1)[0] == 'discretize':
                    numerical_features, categorical_features = PrototypeSingleton.getInstance().getFeatures()
                    operator = ColumnTransformer(
                        transformers=[
                            ('num', Pipeline(steps=[('discretizing', globals()[item[0].split('_', 1)[-1]](**params))]),
                             numerical_features),
                            ('cat', Pipeline(steps=[('identity', FunctionTransformer())]),
                             categorical_features)])
                    PrototypeSingleton.getInstance().discretizeFeatures()
                    operators.append((part, operator))
                else:
                    operator = globals()[item[0].split('_',1)[-1]](**params)
                    operators.append((part, operator))

        PrototypeSingleton.getInstance().resetFeatures()
        clf = algorithm(random_state=seed, **algo_config)
        return Pipeline(operators + [("classifier", clf)]), operators