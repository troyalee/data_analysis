import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from IPython.display import display_html
import more_itertools as mit   


def assign_year_mth_qtr(data):
    mth_dict = {'jan' : '01', 'feb' : '02', 'mar' : '03',
                'apr' : '04', 'may' : '05', 'jun' : '06',
                'jul' : '07', 'aug' : '08', 'sep' : '09',
                'oct' : '10', 'nov' : '11', 'dec' : '12'}
    
    qtr_dict = {'jan' : 'Q1', 'feb' : 'Q1', 'mar' : 'Q1',
                'apr' : 'Q2', 'may' : 'Q2', 'jun' : 'Q2',
                'jul' : 'Q3', 'aug' : 'Q3', 'sep' : 'Q3',
                'oct' : 'Q4', 'nov' : 'Q4', 'dec' : 'Q4'}
    
    unique_mth = data['month'].unique()
    year_list = ['2008','2009','2010']
    
    for month in unique_mth:
        iterable = data[data['month'] == month].index.tolist()
        indice_list = [list(group) for group in mit.consecutive_groups(iterable)]
    
    
        for ind in range(len(indice_list)):
            yr_ind = ind + 1 if month in ['jan','feb','mar','apr','sep'] and len(indice_list) == 2 else ind
            data.loc[indice_list[ind],'year'] = year_list[yr_ind]
    data['quarter'] = data['year'] + data['month'].map(qtr_dict)
    data['month'] = data['month'].map(mth_dict)
    data['date'] = data['year'] + '-' + data['month']
    
    return data


def subscr_rate_by_col(data, colname, ax = None, loc = 1):
    counts = data.groupby(by = [colname,'y']).size().unstack()
    counts['total'] = counts['yes'] + counts['no']
    counts['resp_rate'] = round(counts['yes'] / counts['total'],4)
    
    
    bar_plot = counts[['yes','no']].plot(kind = 'bar', stacked = True, ax=ax, legend = False)
    ln_plot = counts.plot(y = 'resp_rate', label = 'Response Rate', secondary_y = True, 
                           ax=ax, color = 'grey', marker = 'o', lw = 3, legend = False, rot=45)

    plt.title(f'Volume and Response Rate by {colname.upper()}', fontsize = 14)

    bar_plot.set_xlabel(f'{colname.upper()}')
    bar_plot.set_ylabel('Volume')
    ln_plot.set_ylabel('Response Rate')

    h1, l1 = bar_plot.get_legend_handles_labels()
    h2, l2 = ln_plot.get_legend_handles_labels()

    plt.legend(h1+h2, l1+l2, loc = loc)
    
    plt.tight_layout()
    

def profile_generator(data):
    sample_size = len(data)
    
    volume = pd.Series(sample_size, index = ['Volume'])
    avg_age = pd.Series(round(data.age.mean(),1), index = ['Avg. Age'])
    avg_balance = pd.Series('$' + str(round(data.balance.median(),2)), index = ['Median Balance ($)'])
    
    profile_comp = [volume, avg_age]
    cat_var = ['marital','education','job','housing','default','loan']
    
    for var in cat_var:
        if var in ['marital','education','job']:
            temp = round(data.groupby(var).size() / sample_size * 100, 2).apply(lambda x : str(x)+'%')
            temp = pd.Series(temp, index = temp.index)
        else:
            try:
                temp = pd.Series(str(round(data.groupby(var).size()['yes'] / sample_size * 100, 2)) + '%', index = [var])
            except:
                temp = pd.Series('0.00%', index = [var])
                
        profile_comp.append(temp)
    
    profile_comp.append(avg_balance)
    
    profile = pd.concat(profile_comp, axis = 0)
    profile = pd.DataFrame(profile[profile.index != 'unknown'])
    
    index = [('', 'Volume'), ('', 'Avg. Age'), 
             ('Marital Status', 'divorced'), ('Marital Status', 'married'), ('Marital Status', 'single'),
             ('Education', 'primary'), ('Education', 'secondary'), ('Education', 'tertiary'),
             ('Occupation', 'admin.'), ('Occupation', 'blue-collar'), ('Occupation', 'entrepreneur'), 
             ('Occupation', 'housemaid'), ('Occupation', 'management'), ('Occupation', 'retired'),
             ('Occupation', 'self-employed'), ('Occupation', 'services'), ('Occupation', 'student'),
             ('Occupation', 'technician'), ('Occupation', 'unemployed'),
             ('', 'housing'), ('', 'default'), ('', 'loan'), ('', 'Median Balance ($)')
            ]
    
    left_index = pd.MultiIndex.from_tuples(index, names = ['', 'index'])
    
    output = pd.DataFrame(index = left_index).reset_index()
    profile = profile.reset_index()
    
    output = output.merge(profile, how = 'left', on = 'index')
    output = output.set_index(['', 'index'])
    output.index.names = (None, None)
    
    return output


def side_by_side_profile(data, colname, overall = False):
    groups = data[colname].sort_values().unique()
    output = pd.DataFrame()
    
    for idx, group in enumerate(groups):
        profile = profile_generator(data[data[colname] == group])
        output = pd.concat([output, profile], axis = 1).rename(columns = {0 : '{}'.format(group)})
    
    if overall:
        overall_profile = profile_generator(data)
        output = pd.concat([output, overall_profile], axis = 1).rename(columns = {0 : 'Overall'})
    
    return output


def display_side_by_side(*args):
    html_str=''
    for df in args:
        html_str+=df.to_html()
        
    display_html(html_str.replace('table','table style="display:inline"'), raw=True)
    
    
def plot_numeric(data, colname):
    f, ax = plt.subplots(figsize = (7,4))
    
    no_plot = sns.distplot(data.loc[data['y'] == 'no', colname], label = 'Not Subscribed')
    yes_plot = sns.distplot(data.loc[data['y'] == 'yes', colname], label = 'Subscribed')
    
    ax.legend(['Not Subscribed', 'Subscribed'], loc = 1)
    ax.set_ylabel('Probability Density', fontsize = 14)
    ax.set_xlabel('{}'.format(colname.upper()), fontsize = 14)
    ax.set_title('{} by Campaign Response'.format(colname.upper()), fontsize = 16)

    plt.tight_layout()
    
    plt.show()


def roc_plot(model, X_test, y_test):
    probs = model.predict_proba(X_test)
    preds = probs[:,1]
    fpr, tpr, threshold = roc_curve(y_test, preds)
    roc_auc = auc(fpr, tpr)
    
    plt.title('Receiver Operating Characteristic')
    plt.plot(fpr, tpr, 'b', label = 'AUC = %0.2f' % roc_auc)
    plt.legend(loc = 'lower right')
    plt.plot([0, 1], [0, 1],'r--')
    plt.xlim([0, 1])
    plt.ylim([0, 1])
    plt.ylabel('True Positive Rate')
    plt.xlabel('False Positive Rate')