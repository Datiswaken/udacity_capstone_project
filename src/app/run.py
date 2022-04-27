import joblib
import pandas as pd
from typing import Dict, Tuple
from scipy.stats._kde import gaussian_kde as kde_model
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
from src.data.numeric_product_data_attributes import numeric_product_data_attributes
from collections import defaultdict


def load_models() -> Dict[int, Dict[str, Dict[str, kde_model]]]:
    """
    Load all available models

    :return A nested dict containing models for each category, attribute and probability type (low/high)
    """
    models_data = defaultdict(dict)
    for cat_id, attributes in numeric_product_data_attributes.items():
        for attribute in attributes:
            model_low_name = f'{cat_id}_{attribute}_low.pkl'
            model_high_name = f'{cat_id}_{attribute}_high.pkl'

            model_base_path = 'src/model/kde_models/'

            try:
                model_low = joblib.load(model_base_path + model_low_name)
                model_high = joblib.load(model_base_path + model_high_name)

                low_high_dict = {
                    'low': model_low,
                    'high': model_high,
                }

                models_data[cat_id][attribute] = low_high_dict
            except Exception as err:
                print(f'Failed to load model: {str(err)}')

    return models_data


app = Flask(__name__)

engine = create_engine('sqlite:///src/ProductData.db')
df = pd.read_sql_table('model_parameters', engine)

models = load_models()


@app.route('/')
@app.route('/index')
def index():
    data = {
        'title': '',
        'weight': '',
        'width': '',
        'length': '',
        'depth': '',
        'height': '',
        'storage_size': '',
        'screen_size': '',
        'camera_pixel': '',
    }
    return render_template('index.html', data=data)


@app.route('/validate')
def validate():
    category_id = int(request.args.get('category_id', None, type=str))
    weight = request.args.get('weight', None, type=float)
    width = request.args.get('width', None, type=float)
    length = request.args.get('length', None, type=float)
    depth = request.args.get('depth', None, type=float)
    height = request.args.get('height', None, type=float)
    storage_size = request.args.get('storage_size', None, type=float)
    screen_size = request.args.get('screen_size', None, type=float)
    camera_pixel = request.args.get('camera_pixel', None, type=float)
    if camera_pixel:
        camera_pixel *= 1000000

    attributes = models[category_id]
    results = []
    for attribute in attributes.items():
        median = get_attribute_median(f'{category_id}_{attribute[0]}_low')
        result = None
        if (weight or weight == 0) and attribute[0] == 'weight':
            result = get_result_for(weight, median, attribute[1], category_id, 'weight')
        elif width and attribute[0] == 'width':
            result = get_result_for(width, median, attribute[1], category_id, 'width')
        elif length and attribute[0] == 'length':
            result = get_result_for(length, median, attribute[1], category_id, 'length')
        elif depth and attribute[0] == 'depth':
            result = get_result_for(depth, median, attribute[1], category_id, 'depth')
        elif height and attribute[0] == 'height':
            result = get_result_for(height, median, attribute[1], category_id, 'height')
        elif storage_size and attribute[0] == 'storage_size':
            result = get_result_for(storage_size, median, attribute[1], category_id, 'storage_size')
        elif screen_size and attribute[0] == 'screen_size':
            result = get_result_for(screen_size, median, attribute[1], category_id, 'screen_size')
        elif camera_pixel and attribute[0] == 'camera_pixel_max':
            result = get_result_for(camera_pixel, median, attribute[1], category_id, 'camera_pixel_max')

        if result:
            results.append(result)

    return jsonify(results)


@app.route('/import_data', methods=['POST'])
def import_data():
    data = request.form
    # Actual data processing left out on purpose

    return render_template('processed.html')


def get_model_threshold(category_id: int, attribute_name: str, input_value: float, median: float) -> float:
    """
    Get the relevant outlier threshold of a model given the input value

    :param category_id: The category ID
    :param attribute_name: Name of the relevant attribute
    :param input_value: Value provided by the user
    :param median: Median of the attribute

    :return Returns the threshold value of a model
    """
    if input_value <= median:
        model_name = f'{category_id}_{attribute_name}_low'
    else:
        model_name = f'{category_id}_{attribute_name}_high'

    return df['threshold'][df['model'] == model_name].values[0]


def get_attribute_median(model_name: str) -> float:
    """
    Get the median of a model

    :param model_name: Full name of the model as it is stored in the database

    :return Model median
    """
    return df['median'][df['model'] == model_name].values[0]


def get_probability(
        input_value: float,
        attribute_median: float,
        attribute_models_dict: Dict[str, kde_model]
) -> float:
    """
    Get the probability of a given input value on a density function

    :param input_value: Value provided by the user
    :param attribute_median: Median of the attribute
    :param attribute_models_dict: Dictionary containing models for low and high values of given attribute

    :return Probability value
    """
    if input_value <= attribute_median:
        model: kde_model = attribute_models_dict['low']
    else:
        model: kde_model = attribute_models_dict['high']

    return model.pdf(input_value)[0]


def compose_result(
        value_is_outlier: bool,
        attribute_name: str,
        input_value: float,
        median: float
) -> Tuple[bool, str, str]:
    """
    Compose response result for the outlier determination

    :param value_is_outlier: Is the input value considered as an outlier
    :param attribute_name: Name of the relevant attribute
    :param input_value: Value provided by the user
    :param median: Median of the attribute

    :return Tuple containing information about outlier consideration, attribute name and probability type (low/high)
    """
    if input_value <= median:
        return not value_is_outlier, attribute_name, 'low'
    else:
        return not value_is_outlier, attribute_name, 'high'


def get_result_for(
        input_value: float,
        median: float,
        attribute_models_dict: Dict[str, kde_model],
        category_id: int,
        attribute_name: str
) -> Tuple[bool, str, str]:
    """
    Get a result if an input value is considered as an outlier that can be provided to the client

    :param input_value: Value provided by the user
    :param median: Median of the attribute
    :param attribute_models_dict: Dictionary containing models for low and high values of given attribute
    :param category_id: The category ID
    :param attribute_name: Name of the relevant attribute

    :return Tuple containing information about outlier consideration, attribute name and probability type (low/high)
    """
    probability = get_probability(input_value, median, attribute_models_dict)
    threshold = get_model_threshold(category_id, attribute_name, input_value, median)
    value_is_outlier = probability <= threshold

    return compose_result(value_is_outlier, attribute_name, input_value, median)


def main():
    app.run(host='0.0.0.0', port=3001, debug=True)


if __name__ == '__main__':
    main()
