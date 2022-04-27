# Kaufland Product Data Importer
## A project of the Udacity Data Science Nanodegree

## Project Overview
This is the final project of the Udacity Data Science Nanodegree. The project itself is not given
by Udacity, but instead it is up to the user to decide for an own project with its own data and problem
to solve.

I have decided to make use of product data of Kaufland.de a German online marketplace.

The project covers the fundamental steps of a data science project:
- Problem definition
- Data analysis
- Model development
- Model evaluation
- Usage of the model in a web application

## Project Goal
The main goal was to develop a system to automatically detect unusual values of numerical attributes 
for certain product categories. The data is provided by the sellers selling on the marketplace. However,
there are numerous reasons, why this approach can lead to data being not correctly interpreted by the
system. For example the data could be entered with the wrong unit in mind, so the interpreted 
value might be off by several magnitudes from the actual value.

Assuming that the majority of data is entered correctly, those wrong values should appear relatively 
rarely compared to valid values and therefore an outlier detection algorithm should be able to identify
those values.

## Project Structure
The project contains a `src` folder which in turn contains three other folders:
- `app`: Contains code related to the web app
- `data`: Contains a script for preprocessing
- `model`: Contains a script for training the model

Furthermore, the raw dataset (`numeric_attributes_raw.csv`) itself can be found in the root folder

## How to Run
To get started with the project run the following command in the root directory:
1. `pip install -r requirements.txt`
2. `pip install --editable .`
3. `python src/data/preprocessing.py numeric_attributes_raw.csv src/ProductData.db`
4. `python src/model/train_classifiers.py src/ProductData.db src/model/kde_models/`
5. `python src/app/run.py`

Go to http://127.0.0.1:3001/

Note: You need to be within a Python virtual environment:
- Run `python -m venv env` in the root folder
- Afterwards run `source env/bin/activate`

## Libraries
Libraries used for the web application can be found in `requirements.txt`.\
For the data analysis part the following libraries where used:
- pandas
- numpy
- matplotlib
- sklearn
- scipy

## Web Application
The implemented web application simulates a very primitive product data import interface. A seller can decide for which
product category they would like to add an item, e.g. laptops, cell phones, etc. The seller then adds a product title
as well as necessary numerical attributes.\
Before a data can be submitted the data validation must be triggered. This is where the backend makes use of the 
developed outlier detection model to decide, whether the input values for the numerical attributes seem too high or too
low. If so, the seller is informed that they should re-assure that everything is correct.\
Even if the system marks a value as an outlier, it does not prevent the seller from submitting the data. Reasoning is
that there are valid products for which certain attributes are lying outside the normal range. So the system might
mention false positives to the seller.

## Data Analysis
### Dataset
The raw dataset used for this project is about 29 MB and contains 245,613 rows and 13 columns.
The columns are as follows:
- `id_item`: Hashed Item ID
- `category`: Category ID
- `name_category`: Category Name
- `is_valid`: Flag whether the item is valid
- `is_blacklisted`: Flag whether the item has been blacklisted
- `screen_size`: Product screen Size
- `width`: Product width
- `weight`: Product weight
- `height`: Product height
- `length`: Product length
- `depth`: Product depth
- `storage_size`: Storage Size of a data storage device
- `camera_pixel_max`: Camera pixels

### Data Exploration

High level statistics of each numerical attribute is shown in the following image:

![numeric_attributes_statistics](./src/assets/numeric_attributes_statistics.png)

A total of 36,739 items are invalid and 1,977 are blacklisted

The following image shows the count of items in each product category:

![category_counts](./src/assets/category_counts.png)

(Translations: `schreibtische` -> `desks`, `handys` -> `cell phones`, `fernseher` -> `televisions`,
`spiegelreflexkameras-dslr` -> `reflex cameras`)

In the beginning I was interested whether there are actually obvious outliers in the given attributes, so I started
by looking at some box plots:

**Cell Phones**
![cell_phones](./src/assets/cell_phones_boxplot.png)

**Laptops**
![laptops](./src/assets/laptops_boxplot.png)

**Televisions**
![televisions](./src/assets/television_boxplot.png)

As can be seen, there are outliers in all attributes.

At this point I was interested in the distribution of some attributes to get a better decision basis on which 
statistical approach would be best suited to detect those outliers.

Common approaches like Z-scores or interquartile range are only reliable if the given data follows a normal distribution.
However, after checking some attributes' data it was clear, that they are quite skewed to the right and do not follow
a normal distribution.
Therefore, I have decided to go with a non-parametric way: Kernel Density Estimation (KDE). KDE estimates a density curve
over the sample data. With this density curve, represented by a probability density function (PDF), one can calculate
a probability at any given point. A low value means that the probability of being a correct value according to the 
product domain (e.g. a laptop weighing 20 kg) is low and therefore more likely to be considered as an outlier.

Note: Because the products do not have a lot of different numerical attributes, I have decided against using other, 
common machine learning algorithms, which can be used for multidimensional data (e.g. DBSCAN). For one-dimensional data
using KDE seemed to be more suitable.

### Data Cleaning
The following steps have been taken to clean the data:
- Removal of invalid items (certain attributes are missing that are required by the marketplace)
- Removal of blacklisted items
- Removal of possible duplicate items

## Evaluation
This project used an unsupervised machine learning approach and no labeled data was available. For that reason it is not
easily possible to determine objective metrics, like accuracy or precision, for how good the model(s) perform.\
Rather, a more heuristic approach can be taken to evaluate the results.

During the data analysis part I have looked at the plotted data for some attributes. The following shows the 
weight for laptops above the mean (for better visual representation). As can be seen, the outliers (red) are all values 
with higher values, so the model generally seems to work as expected.

![laptops_high_weight](./src/assets/laptop_plot_high.png)

Additionally, by inputting values into the models, i.e. the PDFs for each product attribute, one can get a good feeling
for how well the models work. Based on domain knowledge, e.g. a common laptop does not weight more than a few kilograms,
an evaluation can be done.\
Note, that the thresholds for deciding what values are considered as outliers is somewhat arbitrary. For the sake for
simplicity in this project, I have taken the 1% percentile.

An important factor in KDE that influences how the PDF is calculated, is a parameter called `bandwidth`. See 
[this link](https://aakinshin.net/posts/kde-bw/) for a good explanation of this parameter.
During the data analysis phase I have mostly used the
[KernelDensity](https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KernelDensity.html) module of sklearn.
Changing the `bandwidth` parameter has some effect on the outcome but since every attribute, for each product category, 
needs a potentially different value I have decided to use the 
[gaussian_kde class](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.gaussian_kde.html) of the scipy
package. This class includes automatic bandwidth selection algorithms, like Silverman's rule of thumb.

## Conclusion
Online marketplaces, like Kaufland.de, are sitting on lots of data which they can potentially make use of. However,
the data quality is an important factor. Especially with data input by external parties, e.g. sellers, the quality often
times is not optimal, which prevents an easy usage of it. For that reason it is helpful to have systems in place which
automatically detect wrong data records.\
In the case of numerical attributes those wrong data points can be detected by outlier detection systems.\
Kernel Density Estimation is such a suitable approach to detect outliers in one-dimensional data which is not following a
normal distribution. With the help of KDE it is possible to create a probability density function without much prior 
knowledge about that underlying data.

### Possible Improvement
To determine whether a data point is considered as an outlier a threshold is required which defines the limit for 
outliers. In the current solution the PDF is calculated based on the assumption that the dataset contains outliers
and that ~1% of data points would be considered as such. If the dataset quality would improve over time and the amount
of outliers would decrease, the algorithm would still assume 1% of data points to be outliers, even though they are valid.

