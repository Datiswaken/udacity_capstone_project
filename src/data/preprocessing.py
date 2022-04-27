import sys
import pandas as pd
from pandas import DataFrame
from sqlalchemy import create_engine


def load_data(product_data_filepath: str) -> DataFrame:
    """
    Load the product data from a given filepath

    :param product_data_filepath: The filepath to the product data

    :return Returns the loaded data as a dataframe
    """
    try:
        return pd.read_csv(product_data_filepath)
    except Exception as err:
        print(f'Failed to load data.\nError: {str(err)}')
        sys.exit()


def clean_data(df: DataFrame) -> DataFrame:
    """
    Conduct several data cleaning steps

    :param df: The dataframe for which the data cleaning steps should be conducted

    :return Returns the cleaned dataframe
    """
    df = remove_invalid(df)
    df = remove_blacklisted(df)
    df = drop_duplicate_items(df)

    return df


def drop_duplicate_items(df: DataFrame) -> DataFrame:
    """
    Drop duplicate items. Two items are considered as duplicates, if they have the same item ID

    :param df: The dataframe for which duplicate items should be dropped

    :return Returns the dataframe without duplicate items
    """
    if df.duplicated().sum() > 0:
        df.drop_duplicates(inplace=True)

    return df


def remove_invalid(df: DataFrame) -> DataFrame:
    """
    Remove all rows where 'is_valid' is False

    :param df: The dataframe for which invalid items should be removed

    :return Returns the dataframe with only valid items
    """
    return df[df['is_valid']]


def remove_blacklisted(df: DataFrame) -> DataFrame:
    """
    Remove all rows where 'is_blacklisted' is True

    :param df: The dataframe for which blacklisted items should be removed

    :return Returns the dataframe with only non-blacklisted items
    """
    df = df.dropna(subset=['is_blacklisted'])
    df = df.astype({'is_blacklisted': 'bool'})
    return df[~df['is_blacklisted']]


def store_data(df: DataFrame, database_filename: str) -> None:
    """
    Store a dataframe in an sqlite database

    :param df: The dataframe to be stored
    :param database_filename: The path/filename to the database
    """
    engine = create_engine(f'sqlite:///{database_filename}')
    df.to_sql('product_data', engine, index=False, if_exists='replace')


def main():
    if len(sys.argv) == 3:
        product_data_filepath, database_filename = sys.argv[1:]

        print(f'Loading product data from {product_data_filepath}...')
        df = load_data(product_data_filepath)
        print('Done \u2714')

        print('Cleaning data...')
        df = clean_data(df)
        print('Done \u2714')

        print(f'Storing data in {database_filename}')
        store_data(df, database_filename)
        print('Done \u2714')
    else:
        print('Please provide a filepath to the raw product data '
              'as well as a path/name of the database.')


if __name__ == '__main__':
    main()
