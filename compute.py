from numpy import mean, std, loadtxt, where
import os
import urllib
from scipy import stats
from statsmodels.graphics.factorplots import interaction_plot
import statistics
import matplotlib.pyplot as plt
import pandas as pd
from dataparse import bin_dataframe_generator, bins_subset, DataSet


def compute_mean_std(filename=None):
    data = loadtxt(os.path.join('uploads', filename))
    return """
Data from file <tt>%s</tt>:
<p>
<table border=1>
<tr><td> mean    </td><td> %.3g </td></tr>
<tr><td> st.dev. </td><td> %.3g </td></tr>
""" % (filename, mean(data), std(data))


def check_outliers(filtered, unfiltered):
    comparison = unfiltered.data_set() == filtered.data_set()

    if False in comparison:
        return where(comparison == False)


def display_stat_info(dataset):
    statInfo = "<h3>Statistical Info</h3> <br/>"
    statInfo += "Dataset '{}':".format(dataset.data_name()) + "<br />"
    statInfo += "No. of samples: {}".format(dataset.sampling_size()) + "<br />"

    if dataset.isnormal():
        statInfo += "Mean: {}".format(dataset.mean_value()) + "<br />"
        statInfo += "Standard deviation: {}".format(dataset.std_value()) + "<br />"
        statInfo += "Standard error of the mean: {}\n".format(dataset.sem_value()) + "<br />"
    else:
        statInfo += "Median: {}".format(dataset.median_value()) + "<br />"
        statInfo += "Quantile 25%: {}".format(dataset.quantile25_value()) + "<br />"
        statInfo += "Quantile 75%: {}\n".format(dataset.quantile75_value()) + "<br />"

    return statInfo


def null_hypothesis_tests(datasetA, datasetB):
    statInfo = "<h3>Null Hypothesis Tests</h3> <br/>"
    if datasetA.isnormal() and datasetB.isnormal():
        t_tTest, p_tTest = stats.ttest_ind(datasetA.data_set(), datasetB.data_set())
        statInfo += "Student's t-test results: t = {0}, P = {1}\n".format(t_tTest, p_tTest) + "<br/>"

    else:
        t_tTest, p_tTest = stats.ttest_ind(datasetA.data_set(),
                                           datasetB.data_set())  # performs t-test even if not normal
        u_rankSums, p_rankSums = stats.ranksums(datasetA.data_set(), datasetB.data_set())
        statInfo += "Student's t-test results: t = {0}, P = {1}".format(t_tTest, p_tTest) + "<br/>"
        statInfo += "Wilcoxon rank-sum results: u = {0}, P = {1}".format(u_rankSums, p_rankSums) + "<br/>"
    return statInfo


def normality_tests(datasetA, datasetB):
    statInfo = "<h3>Normality Tests</h3> <br/>"
    wShapiroWilkA, pShapiroWilkA = stats.shapiro(datasetA.data_set())
    statInfo += "Shapiro-Wilk test results for dataset {0}: <br/> W = {1}, P = {2}".format(datasetA.data_name(),
                                                                                           wShapiroWilkA,
                                                                                           pShapiroWilkA) + "<br/>"

    wShapiroWilkB, pShapiroWilkB = stats.shapiro(datasetB.data_set())
    statInfo += "Shapiro-Wilk test results for dataset {0}: <br/> W = {1}, P = {2}".format(datasetB.data_name(),
                                                                                           wShapiroWilkB,
                                                                                           pShapiroWilkB) + "<br/>"

    wLevene, pLevene = stats.levene(datasetA.data_set(), datasetB.data_set())
    statInfo += "Levene test results: <br/> W = {0}, P = {1}".format(wLevene, pLevene) + "<br/>"

    if pShapiroWilkA < 0.05:
        statInfo += "Data set '{}' failed Shapiro-Wilk test.".format(datasetA.data_name()) + "<br/>"
        datasetA._isnormal = False

    if pShapiroWilkB < 0.05:
        statInfo += "Data set '{}' failed Shapiro-Wilk test.".format(datasetB.data_name()) + "<br/>"
        datasetB._isnormal = False

    if pLevene < 0.05:
        statInfo += "Data sets failed Levene normality test.\n" + "<br/>"
        datasetA._isnormal = False
        datasetB._isnormal = False

    return statInfo


# prototype for one-way ANOVA

def one_way_anova(stat_data, dataset, bin_var):
    # counts number of bins for given bin variable
    bin_num = dataset.data_frame().columns.str.contains(bin_var + ' bin ').sum()
    subdataset = DataSet(dataset.data_frame(),
                         dataset.data_frame().columns[dataset.data_frame().columns.get_loc(bin_var +
                                                                                           ' bin 1') + bin_num])
    anova_dataset = bin_dataframe_generator(bins_subset(subdataset.data_frame(), bin_var), bin_var, 3)
    bin_list = anova_dataset['bin'].unique()
    bin_size = [anova_dataset[anova_dataset['bin'] == b][bin_var].shape[0] for b in bin_list]
    bin_avg_size = statistics.mean(bin_size)
    bin_size.insert(0, 0)
    bin_mean = [anova_dataset[anova_dataset['bin'] == b][bin_var].mean() for b in bin_list]
    bin_mean.insert(0, 0)

    # Degrees of freedom - df
    N = len(anova_dataset[bin_var])
    grand_mean = anova_dataset[bin_var].mean()

    df_err = sum(bin_size) - bin_num
    ms_err = sum([sum((anova_dataset[anova_dataset['bin'] == b][bin_var] -
                       bin_mean[b])**2)/(bin_size[b]-1) for b in bin_list]) / bin_num
    ss_err = ms_err * df_err

    ss_means = sum([(bin_mean[b] - grand_mean) ** 2 for b in bin_list])
    ms_between = ss_means / (bin_num - 1) * bin_avg_size

    df_groups = bin_num - 1
    ss_groups = ms_between * N / bin_num
    f_one_way_anova = ms_between / ms_err

    anova_list = [anova_dataset[anova_dataset['bin'] == b][bin_var] for b in bin_list]
    f_one_way_anova, p_one_way_anova = stats.f_oneway(*anova_list)

    results = {'sum_sq': [ss_groups, ss_err, ss_groups + ss_err],
               'df': [df_groups, df_err, ''],
               'F': [f_one_way_anova, '', ''],
               'P': [p_one_way_anova, '', '']}
    columns = ['sum_sq', 'df', 'F', 'P']

    anova_table = pd.DataFrame(results, columns=columns, index=['group', 'error', 'total'])

    return anova_table


def two_way_anova(statData, datasetA, datasetB, parameter, paramValueA, paramValueB, binVariable):
    from statsmodels.formula.api import ols
    from statsmodels.stats.anova import anova_lm
    # from statsmodels.graphics.factorplots import interaction_plot
    # import matplotlib.pyplot as plt
    # import pandas as pd
    # from dataparse import bin_dataframe_generator, bins_subset, DataSet

    binNum = datasetA.data_frame().columns.str.contains(
        binVariable + ' bin ').sum()  # counts number of bins for given bin variable

    subdatasetA = DataSet(datasetA.data_frame(),
                          datasetA.data_frame().columns[statData.columns.get_loc(binVariable + ' bin 1') + binNum])
    subdatasetB = DataSet(datasetB.data_frame(),
                          datasetB.data_frame().columns[statData.columns.get_loc(binVariable + ' bin 1') + binNum])
    binDataSetA = bin_dataframe_generator(bins_subset(subdatasetA.data_frame(), binVariable), binVariable, 3)
    binDataSetB = bin_dataframe_generator(bins_subset(subdatasetB.data_frame(), binVariable), binVariable, 3)
    binDataSetA[parameter] = paramValueA
    binDataSetB[parameter] = paramValueB
    anovaDataSet = binDataSetA.append(binDataSetB)

    fig = interaction_plot(anovaDataSet['bin'],
                           anovaDataSet[parameter],
                           anovaDataSet[binVariable],
                           colors=['red', 'blue'],
                           markers=['D', '^'], ms=10)

    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)

    import base64
    figdata_png = base64.b64encode(figfile.getvalue())

    # Degrees of freedom - df

    N = len(anovaDataSet[binVariable])
    dfA = len(anovaDataSet['bin'].unique()) - 1
    dfB = len(anovaDataSet[parameter].unique()) - 1
    dfAxB = dfA * dfB
    dfWithin = N - (len(anovaDataSet['bin'].unique()) * len(anovaDataSet[parameter].unique()))

    # Sum of squares - ssq (factors A, B and total)

    grand_mean = anovaDataSet[binVariable].mean()
    ssqA = sum([(anovaDataSet[anovaDataSet[parameter] == l][binVariable].mean() - grand_mean) ** 2 for l in
                anovaDataSet[parameter]])
    ssqB = sum(
        [(anovaDataSet[anovaDataSet['bin'] == l][binVariable].mean() - grand_mean) ** 2 for l in anovaDataSet['bin']])
    ssqTotal = sum((anovaDataSet[binVariable] - grand_mean) ** 2)

    # Sum of Squares Within (error/residual)

    bin_meansA = [binDataSetA[binDataSetA['bin'] == d][binVariable].mean() for d in binDataSetA['bin']]
    bin_meansB = [binDataSetB[binDataSetB['bin'] == d][binVariable].mean() for d in binDataSetB['bin']]
    ssqWithin = sum((binDataSetB[binVariable] - bin_meansB) ** 2) + sum((binDataSetA[binVariable] - bin_meansA) ** 2)

    # Sum of Squares Interaction

    ssqAxB = ssqTotal - ssqA - ssqB - ssqWithin

    # Mean Squares

    msA = ssqA / dfA
    msB = ssqB / dfB
    msAxB = ssqAxB / dfAxB
    msWithin = ssqWithin / dfWithin

    # F-ratio

    fA = msA / msWithin
    fB = msB / msWithin
    fAxB = msAxB / msWithin

    # Obtaining p-values

    pA = stats.f.sf(fA, dfA, dfWithin)
    pB = stats.f.sf(fB, dfB, dfWithin)
    pAxB = stats.f.sf(fAxB, dfAxB, dfWithin)

    # table with results from ANOVA

    results = {'sum_sq': [ssqA, ssqB, ssqAxB, ssqWithin],
               'df': [dfA, dfB, dfAxB, dfWithin],
               'F': [fA, fB, fAxB, 'NaN'],
               'PR(>F)': [pA, pB, pAxB, 'NaN']}
    columns = ['sum_sq', 'df', 'F', 'PR(>F)']

    return pd.DataFrame(results, columns=columns,
                        index=[parameter, 'bin',
                               parameter + ':bin', 'Residual']), urllib.parse.quote(figdata_png)


def two_way_anova_repmsr(statData, datasetA, datasetB, parameter, paramValueA, paramValueB, binVariable):
    from statsmodels.formula.api import ols
    from statsmodels.stats.anova import anova_lm
    from statsmodels.graphics.factorplots import interaction_plot
    import matplotlib.pyplot as plt
    import pandas as pd
    from dataparse import bin_dataframe_generator, bins_subset, DataSet

    binNum = datasetA.data_frame().columns.str.contains(
        binVariable + ' bin ').sum()  # counts number of bins for given bin variable

    subdatasetA = DataSet(datasetA.data_frame(),
                          datasetA.data_frame().columns[statData.columns.get_loc(binVariable + ' bin 1') + binNum])
    subdatasetB = DataSet(datasetB.data_frame(),
                          datasetB.data_frame().columns[statData.columns.get_loc(binVariable + ' bin 1') + binNum])
    binDataSetA = bin_dataframe_generator(bins_subset(subdatasetA.data_frame(), binVariable), binVariable, 3)
    binDataSetB = bin_dataframe_generator(bins_subset(subdatasetB.data_frame(), binVariable), binVariable, 3)
    binDataSetA[parameter] = paramValueA
    binDataSetB[parameter] = paramValueB
    anovaDataSet = binDataSetA.append(binDataSetB)

    fig = interaction_plot(anovaDataSet['bin'],
                           anovaDataSet[parameter],
                           anovaDataSet[binVariable],
                           colors=['red', 'blue'],
                           markers=['D', '^'], ms=10)

    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)

    import base64
    figdata_png = base64.b64encode(figfile.getvalue())

    # Degrees of freedom - df

    N = len(anovaDataSet[binVariable])
    dfA = len(anovaDataSet['bin'].unique()) - 1
    dfB = len(anovaDataSet[parameter].unique()) - 1
    dfAxB = dfA * dfB
    dfWithin = N - (len(anovaDataSet['bin'].unique()) * len(anovaDataSet[parameter].unique()))

    # Sum of squares - ssq (factors A, B and total)

    grand_mean = anovaDataSet[binVariable].mean()
    ssqA = sum([(anovaDataSet[anovaDataSet[parameter] == l][binVariable].mean() - grand_mean) ** 2 for l in
                anovaDataSet[parameter]])
    ssqB = sum(
        [(anovaDataSet[anovaDataSet['bin'] == l][binVariable].mean() - grand_mean) ** 2 for l in anovaDataSet['bin']])
    ssqTotal = sum((anovaDataSet[binVariable] - grand_mean) ** 2)

    # Sum of Squares Within (error/residual)

    bin_meansA = [binDataSetA[binDataSetA['bin'] == d][binVariable].mean() for d in binDataSetA['bin']]
    bin_meansB = [binDataSetB[binDataSetB['bin'] == d][binVariable].mean() for d in binDataSetB['bin']]
    ssqWithin = sum((binDataSetB[binVariable] - bin_meansB) ** 2) + sum((binDataSetA[binVariable] - bin_meansA) ** 2)

    # Sum of Squares Interaction

    ssqAxB = ssqTotal - ssqA - ssqB - ssqWithin

    # Mean Squares

    msA = ssqA / dfA
    msB = ssqB / dfB
    msAxB = ssqAxB / dfAxB
    msWithin = ssqWithin / dfWithin

    # F-ratio

    fA = msA / msWithin
    fB = msB / msWithin
    fAxB = msAxB / msWithin

    # Obtaining p-values

    pA = stats.f.sf(fA, dfA, dfWithin)
    pB = stats.f.sf(fB, dfB, dfWithin)
    pAxB = stats.f.sf(fAxB, dfAxB, dfWithin)

    # table with results from ANOVA

    results = {'sum_sq': [ssqA, ssqB, ssqAxB, ssqWithin],
               'df': [dfA, dfB, dfAxB, dfWithin],
               'F': [fA, fB, fAxB, 'NaN'],
               'PR(>F)': [pA, pB, pAxB, 'NaN']}
    columns = ['sum_sq', 'df', 'F', 'PR(>F)']

    return pd.DataFrame(results, columns=columns,
                        index=[parameter, 'bin',
                               parameter + ':bin', 'Residual']), urllib.parse.quote(figdata_png), anovaDataSet
