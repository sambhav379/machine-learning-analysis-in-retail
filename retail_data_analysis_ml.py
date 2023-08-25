# -*- coding: utf-8 -*-
"""Retail data analysis - ML

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vm_9sTpWWl1t7-3U57oi_AbX10DGuAv-

## **Retail Data Analysis Using Machine Learning**

This project uses advanced Machine Learning methods for analysis of Retail based on historical sales data for 45 stores located in different regions - each store contains a number of departments.

## Introduction

Making decisions based on limited history is one of the challenges of modeling retail data. Holidays and major events come once a year, and so does the chance to see how strategic decisions impacted the bottom line. In addition, markdowns are known to affect sales – the challenge of this project is to predict which departments will be affected and to what extent.
Therefore, the main problem I will try to solve in this project is the use of advanced methods of machine learning to:

1. predict the department-wide sales for each store;
2. model the effects of markdowns on holiday weeks;
3. provide recommended actions based on the insights drawn, with prioritization placed on largest business impact.

## DataSet

The statistical data used in this project was obtained from the https://www.kaggle.com/manjeetsingh/retaildataset.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from statsmodels.graphics.tsaplots import acf, pacf, plot_acf, plot_pacf
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn import metrics

from keras.wrappers.scikit_learn import KerasRegressor
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.callbacks import EarlyStopping
from keras.layers import LSTM

"""Let's download retail data that relate to the store, department, and regional activity for the given dates.

"""

df1 = pd.read_csv('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-GPXX0BOFEN/Features%20data%20set.csv', delimiter=',')
df1.dataframeName = 'Features data set.csv'
df1

"""Let's study this DataSet. As we can see, the DataSet consists of 8 190 rows and 12 columns.

- Store - the store number
- Date - the week
- Temperature - average temperature in the region
- Fuel_Price - cost of fuel in the region
- MarkDown1-5 - anonymized data related to promotional markdowns. MarkDown data is only available after Nov 2011, and is not available for all stores all the time. Any missing value is marked with an NA
- CPI - the consumer price index
- Unemployment - the unemployment rate
- IsHoliday - whether the week is a special holiday week

Next, we should download historical sales data which covers the period from 2010-02-05 to 2012-11-01.
"""

df2 = pd.read_csv('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-GPXX0BOFEN/sales%20data-set.csv', delimiter=',')
df2.dataframeName = 'Sales data set.csv'
df2

"""As we can see, this DataSet consists of 421 579 rows and 5 columns.

Within this DataSet, we will find the following information:

- Store - the store number
- Dept - the department number
- Date - the week
- Weekly_Sales -  sales for the given department in the given store
- IsHoliday - whether the week is a special holiday week

The last DataSet contains anonymized information about 45 stores, indicating the type and size of a store.
"""

df3 = pd.read_csv('https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-GPXX0BOFEN/stores%20data-set.csv', delimiter=',')
df3.dataframeName = 'Stores data set.csv'
df3

"""## Data pre-preparation

First of all, we need to merge these three DataSets into one using **[pandas.DataFrame.merge()](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01)**.
"""

df = df1.merge(df3, on = 'Store')
df = df2.merge(df, on = ['Store','Date', 'IsHoliday'])
df

"""Let's study this DataSet. As you can see, it consists of 421 570 rows × 16 columns. The DataSet contains information of different types. We should make sure that Python recognized the data types correctly.

"""

df.info()

"""First of all, let's delete rows that contain empty values:

"""

df=df.fillna(0)

"""As we can see, we should transform the Date columns into the DateTime format. Also the type of Store should be categorical:

"""

df['Date'] = pd.to_datetime(df['Date'])
df['Type'] = df['Type'].astype('category')
df.info()

"""**Since stores and their departments belong to different categories, have different sizes, different quantities and assortments of goods and are located in different parts of the city, it will be a mistake to fit the neural network on all records. Departments located in different parts of the city will have different sales with the same input data. In other words, the information for each department has its own variance. Therefore, for the analysis, it is necessary to identify departments and make an analysis for each of them individually.**

Let's group the Rows by Store, Department and Date.
"""

df.groupby(['Store', 'Dept','Date']).sum()

"""Let's calculate the number of rows for each department:

"""

df[['Store', 'Dept']].value_counts()

"""As you can see, most of the departments have 143 rows. Let's analyze one of them.

"""

St = 24
Dt = 50

"""Let's create a DataSet for a Store: St and for a Department: Dt.

"""

df_d = df[(df['Store']==St) & (df['Dept']==Dt)]
df_d

"""## Predict the department-wide sales

Let's take the field 'Weekly_Sales' for forecasting. First of all, we should visualize this data.
"""

plt.figure
_ = plt.subplots(figsize = (20,10))
_ = plt.xticks(rotation = 60)
_ = sns.lineplot(data = df_d, x = 'Date',y = 'Weekly_Sales', )
_ = plt.title('LinePlot showing the change in Weekly Sales', fontsize=20)
plt.show()

"""Let's visualize how sales change during the holidays.

"""

plt.figure
_ = plt.subplots(figsize = (20,10))
_ = plt.xticks(rotation = 60)
_ = sns.lineplot(data = df_d, x = 'Date',y = 'Weekly_Sales', hue = 'IsHoliday',style = 'IsHoliday', markers = True, errorbar=('ci', 68))
_ = plt.title('LinePlot showing the change in Weekly Sales', fontsize=20)
plt.show()

"""As you can see from the plot, there is no increase in sales on holidays.

For a sales forecast, let's create a separate time series that contains only weekly sales data.

"""

ts = df_d[['Date', 'Weekly_Sales']]
ts = ts.set_index('Date')
ts = ts['Weekly_Sales']
ts

"""If we would like to make a forecast of time series, we can make only an assumption that the data for today depend on the values of previous weeks. In order to check for dependencies, it is necessary to perform a correlation analysis between them. This requires:
1. duplicating the time series of data and moving it vertically down for a certain number of days (lag)
2. deleting the missing data at the beginning and at the end (they are formed by vertical shift (**[pandas.DataFrame.shift()](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.shift.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01)**)
3. calculating the correlation coefficient between the obtained series.

Since this operation should be performed for different values of the lag, it is convenient to create a separate function or use **[statsmodels.graphics.tsaplots.plot_acf()](https://www.statsmodels.org/dev/generated/statsmodels.graphics.tsaplots.plot_acf.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01)**.

Or better we can use [Partial autocorrelation function](https://en.wikipedia.org/wiki/Partial_autocorrelation_function?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01): **[statsmodels.graphics.tsaplots.plot_pacf()](https://www.statsmodels.org/stable/generated/statsmodels.graphics.tsaplots.plot_pacf.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01)**.

This analysis will allow us to determine the lag delay. That is, how many weeks ago sales affected today's sales.

"""

print(pd.Series(acf(ts,nlags=10), name = "Correlation Coeff"))
print(pd.Series(pacf(ts,nlags=10), name = "Partial Correlation Coeff"))


fig, axes = plt.subplots(1,2, figsize=(20,5))
_ = plot_acf(ts, lags=30, ax=axes[0])
_ = plot_pacf(ts, lags=30, ax=axes[1])

"""As can be seen from the charts, we have to use sales for the previous 4 weeks as input parameters.

### DataSet creation

Any forecast model can be shown as a black-box of input - target. The target should be the data of the original time series, and the input values are given for the previous weeks.

To automate this process, let's create a general function for time series transformation into a dataset structure.
"""

def series_to_supervised(in_data, tar_data, n_in=1, dropnan=True, target_dep=False):
    """
    Transformation into a training sample taking into account the lag
     : param in_data: Input fields
     : param tar_data: Output field (single)
     : param n_in: Lag shift
     : param dropnan: Do destroy empty lines
     : param target_dep: Whether to take into account the lag of the input field If taken into account, the input will start with lag 1
     : return: Training sample. The last field is the source
    """

    n_vars = in_data.shape[1]
    cols, names = list(), list()

    if target_dep:
        i_start = 1
    else:
        i_start = 0
    for i in range(i_start, n_in + 1):
        cols.append(in_data.shift(i))
        names += [('%s(t-%d)' % (in_data.columns[j], i)) for j in range(n_vars)]

    if target_dep:
        for i in range(n_in, -1, -1):
            cols.append(tar_data.shift(i))
            names += [('%s(t-%d)' % (tar_data.name, i))]
    else:
        # put it all together
        cols.append(tar_data)
        names.append(tar_data.name)
    agg = pd.concat(cols, axis=1)
    agg.columns = names

    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)

    return agg

"""As mentioned above, the input and output fields are the same when predicting time series, they are only shifted by the lag.
Let's create a dataset:

"""

dataset = series_to_supervised(pd.DataFrame(ts), ts, 4)
dataset

"""As you can see, the first and last columns contain the same target data.
Now we should create input (**X**) and output (**Y**) Datasets for forecasting models.

"""

col = dataset.columns
X, Y = dataset[col[1:-1]], dataset[col[-1]]
print("Input: ", X.columns)
print("Target:", Y.name)

"""### Data normalization

After that, we should normalize all the data. In order to do this, the [**sklearn.preprocessing.MinMaxScaler**](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01) module should be used.
It allows easy normalize [**fit_transform()**](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01#sklearn.preprocessing.MinMaxScaler.fit_transform) and convert back all data: [**fit_transform()**](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01#sklearn.preprocessing.MinMaxScaler.inverse_transform)
"""

scaler_x = MinMaxScaler(feature_range=(0, 1))
scaler_y = MinMaxScaler(feature_range=(0, 1))

scaled_x = scaler_x.fit_transform(X)
scaled_y = scaler_y.fit_transform(Y.values.reshape(-1, 1))

"""After that we will form a training and a test DataSet using [**sklearn.model_selection.train_test_split()**](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.train_test_split.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01) in the ratio of 70/30. Without shuffling. It means that test samples are located at the end of **X** and **Y** DataSets.

As a result we will have:

Input normalized DataSets: **X_train, X_test**

Target normalized DataSets: **y_train, y_test**

"""

from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, test_size=0.3, shuffle=False)

"""All the data is normalized. However, for comparing results we should have real scale data of the training and test DataSets:

"""

res_train = scaler_y.inverse_transform(y_train).flatten()
res_test = scaler_y.inverse_transform(y_test).flatten()

"""Target real scale DataSets: **res_train, res_test**.

### Linear Regression

First of all, we should create a model. We will test three types of models. Linear regression, Multilayer Neural Network with Backpropagation and Long Short-Term Memory Neural Network.
Let's create a [**LinearRegression()**](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01):
"""

regressor = LinearRegression()

"""After that, the model should be fitted on the training DataSet. In order to do this, we will use the function fit().

"""

regressor.fit(x_train, y_train)

"""Then we can test it on the test DataSet and use it for prognostication.

"""

y_pred_test_ln = regressor.predict(x_test)
y_pred_test_ln = scaler_y.inverse_transform(y_pred_test_ln).flatten()

"""Let's analyze the accuracy of the results using **[sklearn.metrics](https://scikit-learn.org/stable/modules/model_evaluation.html?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01)**.

"""

print("Correlation train", regressor.score(x_train, y_train))
print("Correlation test", regressor.score(x_test, y_test))
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred_test_ln))
print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred_test_ln))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, y_pred_test_ln)))

"""As you can see, the result correlation on the test DataSet is very bad. Therefore, we should use another nonlinear model.

### Back Propagation Neural Network

The modern approach to the establishment of complex functional dependencies is the use of neural networks. A classical neural network is a [**multilayer neural network with back propagation**](https://en.wikipedia.org/wiki/Backpropagation?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).

We will use [**keras**](https://keras.io/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01) framework to build this model.
First of all, we should create a Neural Network model as a separate function.

A neural network is a sequence of layers. The function [**Sequential()**](https://keras.io/guides/sequential_model/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01) is used to create a network.

Let's create a network that consists of 2 hidden layers. Each of which consists of 100 neurons. [**keras.layers.Dense()**](https://keras.io/api/layers/core_layers/dense/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).

To avoid retraining problems, we will use additional layers [**keras.layers.Dropout()**](https://keras.io/api/layers/regularization_layers/dropout/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).

The output layer will consist of one neuron, since we have only one value at the output.

Model should be compiled for fitting and predicting: [**keras.Model.compile()**](https://keras.io/api/models/model_training_apis/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).
"""

def BP_model(X):
    """
    Multilayer neural network with back propagation .
    :param X: Input DataSet
    :return: keras NN model
    """
    # create model
    model = Sequential()
    model.add(Dense(100, input_dim=X.shape[1], kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(100, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1, kernel_initializer='normal'))
    # Compile model
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

"""Once the model function is built, it is necessary to create a neural network directly and specify the learning parameters: [**keras.wrappers.scikit_learn.KerasRegressor()**](https://keras.io/zh/scikit-learn-api/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01). Also we should specify the number of fitting [**epoch and batch size**](https://machinelearningmastery.com/difference-between-a-batch-and-an-epoch/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).

"""

epochs = 1000
batch_size=int(y_train.shape[0]*.1)
estimator = KerasRegressor(build_fn=BP_model, X=x_train, epochs=epochs, batch_size=batch_size, verbose=1)

"""Now, let’s train our model for **1000** epochs.
It should be noted, that fitting process is very slow. To avoid overfitting and decrease the time of fitting, we will use **[EarlyStopping()](https://keras.io/api/callbacks/early_stopping/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01)** function, that will control the value of the loss function. This function will stop the fitting process when the loss function stop decreasing during 10 iteration. After that, there will be a rollback of all weight parameters to their state that was 10 iteration before.

"""

es = EarlyStopping(monitor='val_loss', mode='auto', patience=10, verbose=1,  restore_best_weights=True)
history=estimator.fit(x_train,y_train, validation_data=(x_test,y_test), callbacks=[es]) # Fitting model

"""Let's show [**loss and validation loss dynamics**](https://machinelearningmastery.com/learning-curves-for-diagnosing-machine-learning-model-performance/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).

"""

plt.figure()
plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='test')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend()
plt.show()

"""As you can see, Neural Network is fitting well and no overfitting is observed.
Let's calculate prediction of the training (**res_train_ANN**) and test (**res_test_ANN**) sets.

Let's calculate the forecast and make inverse normalization to real scale.
"""

res_tr=estimator.predict(x_train)
res_ts=estimator.predict(x_test)
res_train_ANN=scaler_y.inverse_transform(res_tr.reshape(-1, 1)).flatten()
res_test_ANN=scaler_y.inverse_transform(res_ts.reshape(-1, 1)).flatten()

"""Let's compare the accuracy of Linear Regression and Neural Network.

"""

print("Correlation train", np.corrcoef(res_train, res_train_ANN)[0,1])
print("Correlation train", np.corrcoef(res_test, res_test_ANN)[0,1])
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, res_test_ANN))
print('Mean Squared Error:', metrics.mean_squared_error(y_test, res_test_ANN))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, res_test_ANN)))

"""You can see, that the results we got for Neural Network are a little better than ones for Linear Regression. Let's try to use recurrent neural network.

### Long Short-Term Memory - LSTM

Unlike standard feedforward neural networks, an [**LSTM**](https://en.wikipedia.org/wiki/Long_short-term_memory?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01) has feedback connections. It can not only process single data points, but also entire sequences of data (such as speech, video or time series).

In the case of a time series, the neural network has one input and one output. However, the vector of time series values for the previous moments of time is fed to the input.

<center>
    <img src="https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-GPXX0BOFEN/RNN.png" width="1000" alt="cognitiveclass.ai logo">
</center>

To do this, we should transform the input DataSets into 3D shape.
"""

train_x_LSTM = x_train.reshape((x_train.shape[0], 1, 4))
test_x_LSTM = x_test.reshape((x_test.shape[0], 1, 4))

"""Let's create an LSTM Neural Network that consists of one [**LSTM**](https://keras.io/api/layers/recurrent_layers/lstm/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01) layer and one BP layer like in the previous case.
As you can see, in this case our NN will consist of 100 LSTM and 100 BP neurons.

"""

batch_size=int(y_train.shape[0]*.1)
model = Sequential()
model.add(LSTM(100, input_shape=(train_x_LSTM.shape[1], train_x_LSTM.shape[2])))
model.add(Dropout(0.2))
model.add(Dense(100, kernel_initializer='normal', activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(y_train.shape[1])) #activation='sigmoid'
model.compile(loss='mean_squared_error', optimizer='adam')

"""All subsequent steps of learning and predicting are similar to the previous neural network.

"""

history = model.fit(train_x_LSTM, y_train, epochs=epochs, batch_size=batch_size, validation_data=(test_x_LSTM, y_test), verbose=1, shuffle=False, callbacks=[es])

"""Let's plot the dynamic of loss and val loss like in the previous case.

"""

plt.figure()
plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='test')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend()
plt.show()

"""Let's calculate our forecast.

"""

##YOUR CODE GOES HERE##
res_tr_LSTM = model.predict(train_x_LSTM)
res_ts_LSTM = model.predict(test_x_LSTM)
res_train_LSTM=scaler_y.inverse_transform(res_tr_LSTM).flatten()
res_test_LSTM=scaler_y.inverse_transform(res_ts_LSTM).flatten()

"""And accuracy:

"""

print("Correlation train", np.corrcoef(res_train, res_train_LSTM)[0,1])
print("Correlation train", np.corrcoef(res_test, res_test_LSTM)[0,1])
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, res_test_LSTM))
print('Mean Squared Error:', metrics.mean_squared_error(y_test, res_test_LSTM))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, res_test_LSTM)))

"""As you can see, the forecast results of the test data set are the same like in the previous models. Let's visualize these 3 results:

"""

res_pred_test_ln = pd.Series(y_pred_test_ln, name = 'Predicted test Linear Model')
res_pred_test_ANN = pd.Series(res_test_ANN, name = 'Predicted test ANN')
res_pred_test_LSTM = pd.Series(res_test_LSTM, name = 'Predicted test LSTM')

df_2 = pd.DataFrame({'Actual test': res_test, 'Linear Model': res_pred_test_ln, 'ANN Model': res_pred_test_ANN,  'LSTM Model': res_pred_test_LSTM,})
df_2.index = dataset.index[len(dataset)-len(res_test):]
df_2.plot()
plt.show()

"""As you can see, all forecasting shows similar results.

None of the models can predict large peaks. However, the positions of the peaks coincide for all the models. That is, this approach allows you to make adequate models. The accuracy of the forecast depends on additional factors which we will try to consider in the next section.

## Model the effects of markdowns on holiday weeks

To take into account the impact of markdowns on sales on holidays, we should first build a model of sales forecasting depending on other input parameters.

Let's set Date as the index field in our DataSet.
"""

df_d = df_d.set_index('Date')
df_d

"""Next, we should leave only those fields that affect weekly sales and remove the others. In particular, fields such as 'Store', 'Dept', 'Type' are for information only. Field 'Size' remains a constant for a specific department, and therefore cannot be used for modeling, even if it affects the sales.

"""

df_d.columns

df_d = df_d[['Weekly_Sales', 'IsHoliday', 'Temperature',
       'Fuel_Price', 'MarkDown1', 'MarkDown2', 'MarkDown3', 'MarkDown4',
       'MarkDown5', 'CPI', 'Unemployment']]
df_d

"""Let's use the function my_headmap to investigate the correlation between these fields:

> Indented block



"""

def my_headmap(corr):
    '''
    Input:
    corr: correlation matrix in DataFrame
    '''
    # Generate a mask for the upper triangle because it contains duplicate information
    mask = np.triu(np.ones_like(corr, dtype=bool))

    # Set up the matplotlib figure
    f, ax = plt.subplots(figsize=(11, 9))

    # Draw the heatmap with the mask and correct aspect ratio
    sns.heatmap(corr, mask=mask, cmap='RdYlGn', vmin=-1., vmax=1., annot=True, center=0,
                square=True, linewidths=.5, cbar_kws={"shrink": .5})

my_headmap(df_d.corr())

"""As you can see there are no fields that lineary impact on Weekly Sales.

Let's create our DataSet. To do this, join our historical 4 weeks sales data to this dataset.
"""

df_hp = df_d.join(dataset[dataset.columns[1:-1]])
df_hp = df_hp.dropna()
df_hp

"""Let's create the input and target fields:

"""

col = df_hp.columns
X, Y = df_hp[col[1:]], df_hp[col[0]]
print("Input: ", X.columns)
print("Target:", Y.name)

"""Normalize them:

"""

scaler_x = MinMaxScaler(feature_range=(0, 1))
scaler_y = MinMaxScaler(feature_range=(0, 1))
scaled_x = scaler_x.fit_transform(X)
scaled_y = scaler_y.fit_transform(Y.values.reshape(-1, 1))

"""And split them into training and test sets:

"""

x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, test_size=0.3, shuffle=False)

"""We make inverse transform to get the training and test sets in real scale.

"""

res_train = scaler_y.inverse_transform(y_train).flatten()
res_test = scaler_y.inverse_transform(y_test).flatten()

"""### Linear model

Let's create a Linear model for comparing the results:
"""

regressor = LinearRegression()

regressor.fit(x_train, y_train)

y_pred_test_ln = regressor.predict(x_test)
y_pred_test_ln = scaler_y.inverse_transform(y_pred_test_ln).flatten()

print("Correlation train", regressor.score(x_train, y_train))
print("Correlation test", regressor.score(x_test, y_test))
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred_test_ln))
print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred_test_ln))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, y_pred_test_ln)))

"""As you can see, the results are very bad too.

### Back propagation Neural Network

Let's use the same Neural Network as in the previous task.
"""

def BP_model(X):
    """
    Multilayer neural network with back propagation .
    :param X: Input DataSet
    :return: keras NN model
    """
    # create model
    model = Sequential()
    model.add(Dense(100, input_dim=X.shape[1], kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(50, kernel_initializer='normal', activation='relu'))
    model.add(Dropout(0.2))
    model.add(Dense(1, kernel_initializer='normal'))
    # Compile model
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

epochs = 1000
batch_size=int(y_train.shape[0]*.1)
estimator = KerasRegressor(build_fn=BP_model, X=x_train, epochs=epochs, batch_size=batch_size, verbose=0)

"""We will use the same EarlyStopping function.

"""

es = EarlyStopping(monitor='val_loss', mode='auto', patience=10, verbose=1, restore_best_weights=True)
history=estimator.fit(x_train,y_train, validation_data=(x_test,y_test), callbacks=[es])

"""Let's show [**loss and validation loss dynamics**](https://machinelearningmastery.com/learning-curves-for-diagnosing-machine-learning-model-performance/?utm_medium=Exinfluencer&utm_source=Exinfluencer&utm_content=000026UJ&utm_term=10006555&utm_id=NA-SkillsNetwork-Channel-SkillsNetworkGuidedProjectsIBMGPXX0BOFEN347-2022-01-01).

"""

plt.figure()
plt.plot(history.history['loss'], label='train')
plt.plot(history.history['val_loss'], label='test')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend()
plt.show()

"""As you can see, the Neural Network is fitting well and no overfitting is observed.
Let's calculate the prediction of training (**res_train_ANN**) an test (**res_test_ANN**) sets.

Let's calculate a forecast and make inverse normalization to real scale.
"""

res_tr=estimator.predict(x_train)
res_ts=estimator.predict(x_test)
res_train_ANN=scaler_y.inverse_transform(res_tr.reshape(-1, 1)).flatten()
res_test_ANN=scaler_y.inverse_transform(res_ts.reshape(-1, 1)).flatten()

"""Let's compare the accuracy of Linear Regression and Neural Network.

"""

print("Correlation train", np.corrcoef(res_train, res_train_ANN)[0,1])
print("Correlation train", np.corrcoef(res_test, res_test_ANN)[0,1])
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, res_test_ANN))
print('Mean Squared Error:', metrics.mean_squared_error(y_test, res_test_ANN))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, res_test_ANN)))

"""As you can see, the forecast results of the test data set are much better than ones of the previous models. Let's visualize these 2 results:

"""

res_pred_test_ln = pd.Series(y_pred_test_ln, name = 'Predicted test Linear Model')
res_pred_test_ANN = pd.Series(res_test_ANN, name = 'Predicted test ANN')

df_2 = pd.DataFrame({'Actual test': res_test, 'Linear Model': res_pred_test_ln, 'ANN Model': res_pred_test_ANN})
df_2.index = df_d.index[len(df_d)-len(res_test):]
df_2.plot()
plt.show()

"""As you can see from the plot, an ANN shows better results.

Let's calculate the sensitivity of week sales for other factors.

### Sensitivity analysis

We can modify the function, adding regressor model as an input parameter. It will allow us to use this function for any types of regressors.
"""

def my_sens(regressor, x, c, p):
    '''
    Input:
    x: DataFrame of input Linear Regression
    y: Series of output Linear Regression
    p: Percentage of price change
    Return:
    Sensitivity of target
    '''
    X = x[-1:].copy()
    y_pred = regressor.predict(X)
    X[0][c] = X[0][c]*(1+p)
    y_pred_delta = regressor.predict(X)
    return ((y_pred_delta - y_pred) / y_pred)

"""Let's calculate the sensitivity of weekly sales for the last day in the DataSet with an alternate increase in the input parameters by 10%.

"""

for i,c in enumerate(df_hp.columns[2:]):
    print("Sensitivity of Week Sales on %s: %5.2f%%" % (c, my_sens(estimator, x_test, i+1,  0.1) * 100))

"""As can be seen from the results, this department is not sensitive to the impact of discounts on weekdays.

Let's analyze the impact of markdowns during the holiday week. To do this, we will create an input matrix that contains only information about the holidays.
"""

x_test2 = [list(x) for x in x_test if x[0]>=0.99]
x_test2 = np.array(x_test2)

for i,c in enumerate(df_hp.columns[2:]):
    print("Sensitivity of Week Sales in Holiday on %s: %5.2f%%" % (c, my_sens(estimator, x_test2, i+1,  0.1) * 100))

"""As you can see, the holiday week is not sensitive for markdowns too.

## Recommendation for department

As can be seen from the sensitivity analysis for this department, the most significant is the MarkDown5. The other types of discounts either do not affect or, conversely, can have the opposite effect (MarkDown1).

A very interesting is that the sales of this department are very sensitive to temperature. Along with the temperature increase, sales increase sharply both in the holiday and regular weeks. Therefore, the weather forecast should be taken into account in this case.

It can also be seen that the sales intensity of this department have 2 weeks cycle, which is probably related to the type of goods. This means that sales increase will stimulate future sales.

1. Create a function that will analyze the sensitivity of weekly sales in holiday days for any department.
2. Apply this function for one department on your choice.
3. Calculate the sensitivity for any 10 departments, that have 143 rows in the DataSet.
"""

def sens_holiday(df, St, Dt):
    # DataSet creation
    df_d = df[(df['Store']==St) & (df['Dept']==Dt)]

    # Week Sales Time Series creation
    ts = df_d[['Date', 'Weekly_Sales']]
    ts = ts.set_index('Date') ts = ts['Weekly_Sales']

    # Week Sales DataSet creation
    ts_dataset = series_to_supervised(pd.DataFrame(ts), ts, 4)
    df_d = df_d.set_index('Date')
    df_d = df_d[['Weekly_Sales', 'IsHoliday', 'Temperature', 'Fuel_Price', 'MarkDown1', 'MarkDown2', 'MarkDown3', 'MarkDown4', 'MarkDown5', 'CPI', 'Unemployment']]
    df_hp = df_d.join(ts_dataset[ts_dataset.columns[1:-1]])
    df_hp = df_hp.dropna()

    # Splitting on Input and Target
    col = df_hp.columns
    X, Y = df_hp[col[1:]], df_hp[col[0]]

    # Normalization
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    scaled_x = scaler_x.fit_transform(X)
    scaled_y = scaler_y.fit_transform(Y.values.reshape(-1, 1))

    # Creation Train and Test DataSets
    x_train, x_test, y_train, y_test = train_test_split(scaled_x, scaled_y, test_size=0.3, shuffle=False)

    # Real scale target
    res_train = scaler_y.inverse_transform(y_train).flatten()
    res_test = scaler_y.inverse_transform(y_test).flatten()

    # ANN Creation and fitting
    epochs = 1000
    batch_size=int(y_train.shape[0]*.1)
    estimator = KerasRegressor(build_fn=BP_model, X=x_train, epochs=epochs, batch_size=batch_size, verbose=0)
    es = EarlyStopping(monitor='val_loss', mode='auto', patience=10, verbose=1, restore_best_weights=True)
    history=estimator.fit(x_train,y_train, validation_data=(x_test,y_test), callbacks=[es])

    # Creation Holidays DataSet
    x_test2 = [list(x) for x in x_test if x[0]>=0.99] x_test2 = np.array(x_test2)

    # Sensitivity calculation
    res = {}
    res['Store'] = [St]
    res['Department'] = [Dt]
    for i,c in enumerate(df_hp.columns[2:]):
       res[c] = ["{:.2f}%".format(my_sens(estimator, x_test2, i+1, 0.1)*100)]
    res = pd.DataFrame(res)
    res = res.set_index(['Store', 'Department'])
    return res

"""### Sensitivity of Department

"""

sens_holiday(df, 1, 1)

"""###Sensitivity of 10 departments

"""

# filter departments with 143 rows
depts = df[['Store', 'Dept']].value_counts() depts = depts[depts == 143] depts.name = 'rows' depts

# shuffle depts
depts = depts.reset_index() shuffled_dt = depts.reindex(np.random.permutation(depts.index)) shuffled_dt

# sensitivity calculation
sens = pd.DataFrame() for v in shuffled_dt.values[:10]: print('Store:', v[0], 'Department:', v[1]) sens = sens.append(sens_holiday(df, v[0], v[1]))

sens

"""## Conclusions

During this project, we demonstrated how to analyze and forecast store sales.

It was shown how to use autocorrelation analysis to find time lag delays. We studied how to transform a DataSet to take into account time delays in data.
It was shown how to use linear models, backpropagation neural networks and recurrent neural networks to predict time series on the example of week sales of the store department.

It was shown how to build combined DataSets containing both lag delays and store activity data.
On the basis of a neural network, the influence of markdowns in the store on sales both during the holiday and regular weeks was analyzed.  A sales strategy for a specific department was proposed.
"""