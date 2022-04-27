import sys
import pandas as pd
import numpy as np
import pickle
import time
from pandas import DataFrame
from scipy import stats
from scipy.stats._kde import gaussian_kde as kde_model
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String
from src.data.numeric_product_data_attributes import numeric_product_data_attributes
from typing import List, Tuple
from pathlib import Path


def load_data(database_filename: str) -> DataFrame:
    """
    Load all product data from the database

    :param database_filename: The path/filename to the database

    :return Returns a dataframe containing the product data
    """
    engine = create_engine(f'sqlite:///{database_filename}')
    return pd.read_sql('SELECT * FROM product_data', engine)


def build_models(df: DataFrame) -> List[Tuple[kde_model, str, float, float]]:
    """
    Create two KDE models for each attribute per category. One for values below and one for values above the median

    :param df: The dataframe containing data to build the KDE models

    :return Returns a list of tuples. Each tuple contains a KDE model, the filename of the model, a threshold and median
    """
    kde_models = []
    start_total_time = time.time()
    for cat_id, attributes in numeric_product_data_attributes.items():
        cat_data = df[df['category'] == cat_id]
        print(f'Building models for category {cat_id}...')
        cat_start_time = time.time()
        for attribute in attributes:
            print(f'Current attribute: {attribute}')
            attr_start_time = time.time()
            attribute_data = cat_data[attribute]
            median = attribute_data.median()

            lower_end = attribute_data.where(attribute_data <= median).dropna()
            higher_end = attribute_data.where(attribute_data >= median).dropna()

            kernel_density_low = stats.gaussian_kde(lower_end, bw_method='silverman')
            kernel_density_high = stats.gaussian_kde(higher_end, bw_method='silverman')

            scores_low = kernel_density_low.evaluate(lower_end)
            threshold_low = np.quantile(scores_low, .01)

            scores_high = kernel_density_high.evaluate(higher_end)
            threshold_high = np.quantile(scores_high, .01)

            model_low_filename = f'{cat_id}_{attribute}_low'
            model_high_filename = f'{cat_id}_{attribute}_high'

            kde_models.append((kernel_density_low, model_low_filename, threshold_low, median))
            kde_models.append((kernel_density_high, model_high_filename, threshold_high, median))

            attr_end_time = time.time()
            print(f'Finished with attribute {attribute}. Elapsed time: {attr_end_time - attr_start_time} seconds')

        cat_end_time = time.time()
        print(f'Finished with category {cat_id}. Elapsed time: {cat_end_time - cat_start_time} seconds')

    end_total_time = time.time()
    print(f'Total time for building models: {end_total_time - start_total_time} seconds.')

    return kde_models


def save_model_parameter(model_filename: str, threshold: float, median: float, database_filename: str) -> None:
    """
    Save the threshold and median for a given model in the database

    :param model_filename: Filename of the model
    :param threshold: Threshold for the given model
    :param median: Median for the given model
    :param database_filename: The path/filename to the database
    """
    engine = create_engine(f'sqlite:///{database_filename}')
    query = """INSERT INTO model_parameters (model,threshold,median)
            VALUES (?,?,?) ON CONFLICT(model) DO
            UPDATE SET threshold=?, median=?
    """
    parameters = (model_filename, threshold, median, threshold, median)
    engine.execute(query, parameters)


def init_thresholds_table(database_filename: str) -> None:
    """
    Create a table 'model_parameters' which stores the model filename, threshold and median for each model

    :param database_filename: The path/filename to the database
    """
    engine = create_engine(f'sqlite:///{database_filename}')
    meta = MetaData()
    Table(
        'model_parameters', meta,
        Column('id', Integer, primary_key=True),
        Column('model', String, unique=True),
        Column('threshold', Float),
        Column('median', Float)
    )

    meta.create_all(engine)


def save_models_and_parameters(models: List[Tuple], filepath: str, database_filename: str) -> None:
    """
    Save the models themselves and corresponding parameters

    :param models: List of tuples containing the KDE model, model filename, threshold and median
    :param filepath: Filepath to the KDE models
    :param database_filename: The path/filename to the database
    """
    for model in models:
        save_model(model[0], filepath, model[1])
        save_model_parameter(model[1], model[2], model[3], database_filename)


def save_model(model: kde_model, filepath: str, filename: str) -> None:
    """
    Save model files to a given filepath

    :param model: The model to be saved
    :param filepath: Filepath where the model should be saved to
    :param filename: Filename of the model
    """
    Path(filepath).mkdir(parents=True, exist_ok=True)
    full_filepath = f'{filepath}/{filename}.pkl'
    file = open(full_filepath, 'wb')
    pickle.dump(model, file)
    file.close()


def main():
    if len(sys.argv) == 3:
        database_filename, model_filepath = sys.argv[1:]

        init_thresholds_table(database_filename)

        print(f'Loading product data from database: {database_filename}...')
        df = load_data(database_filename)
        print('Done \u2714')

        print('Building models...')
        models = build_models(df)
        print('Done \u2714')

        print(f'Saving models under path {model_filepath} and storing thresholds in {database_filename}...')
        save_models_and_parameters(models, model_filepath, database_filename)
        print('Done \u2714')

    else:
        print('Please provide a path/name of the database to load data from as well as a path where to store the '
              'trained models')


if __name__ == '__main__':
    main()
