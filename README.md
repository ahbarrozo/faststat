# faststat
Flask-based web server for statistical analysis. Allows the usage of multiple statistical analysis tools, such as Normality Tests (Levene or Shapiro-Wilk), Null-Hypothesis Test (Student's t-test), and ANOVA (One and two-way). The app was built to facilitate report writing, where every calculation can be storede in a local database for later use. The user is encouraged to create her/his own account for this purpose.
This webapp allows users to input an Excel spreadsheet, and the app will parse the data, removing outliers using Smirnov-Grubbs test. Currently, the app works with a specific spreadsheet format. This will hopefully be fixed in the future.

### How to install  

This code was developed in Python 3.8. However, it should work for 3.7 as well. To install all the required packages, simply run the following command in the `faststat` folder

``` 
pip install -r requirements.txt
```

### How to run

This webapp can be executed locally by running
```
python run.py
```

A URL will be generated, which can be pasted in any browser.
