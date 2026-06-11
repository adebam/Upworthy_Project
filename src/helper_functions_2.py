#basics
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

#stats
from scipy.stats import chisquare
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.proportion import proportions_ztest
from scipy.stats import dunnett
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.multitest import multipletests

#others
import math
import os
from pathlib import Path
from IPython.display import HTML, display


def confidence_interval_plot(p_val, control_ctr, treatment_ctr, control_lower, control_upper, treatment_lower, treatment_upper , alpha,alpha_significant_str,test_id):
    """
    This is just a plot for the confidence interval. 
    f"A/B Test Results: CTR with {alpha_significant_str}"
    """

    c_err = [np.abs([control_ctr - control_lower]), np.abs([control_upper - control_ctr])]
    t_err = [np.abs([treatment_ctr - treatment_lower]), np.abs([treatment_upper - treatment_ctr])]

    # Specify parameters for CI plots
    output_dir = "confidence_interval_plot"
    os.makedirs(output_dir, exist_ok=True)
    
    #Apply a clean design style
    sns.set_theme(style="whitegrid")
    plt.rc('font', family='sans-serif', size=11)
    colors = 'red' if p_val < alpha else "royalblue"
    
    # Initialize the plot 
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot Control Point and Error Bar
    #ax.errorbar(x=row['Variant CTR %'], y=i, xerr=[[row['error_left']], [row['error_right']]], fmt='o', color=colors[i], markersize=8, capsize=5,  capthick=1.5, linewidth=2,label='Variants' if row['Relative Lift %'] != 0 else 'Control')
    #ax.errorbar(x='Control', y=control_ctr, xerr=c_err, fmt='o', color='royalblue', markersize=8, capsize=6, elinewidth=2, label='Control')
    ax.errorbar(x=control_ctr, y='Control', xerr=c_err,  fmt='o', color='black', markersize=8, capsize=6, elinewidth=2)

    # Plot Treatment Point and Error Bar
    #ax.errorbar(x='Treatment', y=treatment_ctr, xerr=t_err, fmt='o', color='darkorange', markersize=8, capsize=6, elinewidth=2, label='Treatment')
    ax.errorbar(x=treatment_ctr, y='Treatment', xerr=t_err, fmt='o', color=colors, markersize=8, capsize=6, elinewidth=2)
    
    # --- 6. Style and Annotate the Chart ---

    plt.xlabel('Click-Through Rate (CTR) %', fontsize=12)
    plt.title(f"A/B Test Results: Click-Through Rate (CTR) with {(1-alpha)*100}% Confidence Intervals", fontsize=12, fontweight='bold')

    c_label_text = f"{control_ctr:.3f} (Control)"
    ax.text(x=control_upper + 0.001, y='Control', s=c_label_text, va='center', ha='left', fontsize=10, fontweight='bold', color='black')

    t_label_text = f"{treatment_ctr:.3f} (Treatment)"
    ax.text(x=treatment_upper + 0.001, y="Treatment", s=t_label_text, va='center', fontsize=10, fontweight='bold', color=colors )

    #Draw a vertical reference line for the Control Baseline
    ax.axvline(x=control_ctr, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.5, label='Control Value') # this alpha is to control the color
    

    # Convert X-axis values to percentages for readability
    plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.2%}'))
    
    # Adjust the y-axis padding so the labels look clean
    plt.ylim(-0.5, 1.5)
    
    # Add subtle vertical gridlines for tracking horizontal overlap
    plt.grid(axis='x', linestyle='--', alpha=0.5)

    # UPDATED LEGEND HANDLING (CUSTOM HANDLES)
    legend_elements = [
        Line2D([0], [0], marker='o', color='black', label='Control', markersize=8, linestyle='None'),
        Line2D([0], [0], marker='o', color=colors, label='Treatment', markersize=8, linestyle='None'),
        Line2D([0], [0], color='#E74C3C', linestyle='--', linewidth=1.5, label='Control Baseline')
    ]
    # Apply the explicit legend to the axis
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, facecolor='white', edgecolor='none')

    plt.tight_layout()
    #plt.show()

    
    file_name = f"CI_plots_{test_id}.png"
    file_path = os.path.join(output_dir, file_name)
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()  # Prevents plot from popping up now

    # Convert the file path into a clickable HTML link string
    # target="_blank" makes it open in a new browser tab when clicked
    web_path = f"confidence_interval_plot/{file_name}"
    return f'<a href="{web_path}" target="_blank" rel="noopener noreferrer">View Plot</a>'


def Run_Individual_Proportion_Z_Test(df_all, alpha,  variable_to_test):
    test_results = []
    alpha_significant_str=f"Significant (α={alpha})?"
    
    for test_id, group in df_all.groupby('clickability_test_id'):
        # Isolate splits
        ctrl = group[group[variable_to_test] == 0]
        treat = group[group[variable_to_test] == 1]
    
        # Skip if the test doesn't have both a control and a treatment variation
        if ctrl.empty or treat.empty:
            continue
            
        c_clicks, c_impr = ctrl['clicks'].sum(), ctrl['impressions'].sum()
        t_clicks, t_impr = treat['clicks'].sum(), treat['impressions'].sum()
    
        # Ensure there is enough traffic to run a test
        if c_impr == 0 or t_impr == 0:
            continue
    # Run individual test
        try:
            count = np.array([t_clicks, c_clicks])
            nobs = np.array([t_impr, c_impr])
            control_ctr = c_clicks / c_impr
            treatment_ctr=t_clicks / t_impr
            
            _, p_val = proportions_ztest(count, nobs, alternative="two-sided") # two-sided : is there a difference btw the treatment and control larger: is treatment greater than control
            # CI calculation
            #Control CTR Confidence Interval
            control_lower, control_upper = proportion_confint(count=c_clicks, nobs=c_impr, alpha=alpha, method='wilson')
            #Treatment CTR Confidence Interval
            treatment_lower, treatment_upper = proportion_confint(count=t_clicks, nobs=t_impr,  alpha=alpha, method='wilson')
            # call the plot function to plot the CI
            #plot_CI=confidence_interval_plot(p_val, control_ctr, treatment_ctr, control_lower, control_upper, treatment_lower, treatment_upper , alpha,alpha_significant_str,test_id)
            plot_CI=None
            
    
            test_results.append({
                'clickability_test_id': test_id,
                'control_ctr': c_clicks / c_impr,
                'treatment_ctr': t_clicks / t_impr,
                'p_value': p_val,
                'significant': p_val < alpha,
                "CI_plot":plot_CI
            })
        except Exception as e:
            # DO NOT SILENTLY PASS. Print the error so you know what is broken!
            print(f"Skipping test_id {test_id} due to error: {e}")
            continue
    
    summary_df = pd.DataFrame(test_results)
    # Assign the p_value from the dataframe
    p_values = summary_df['p_value'].values
    
    #################################################
    # Apply the Benjamini-Hochberg (fdr_bh) correction
    ##################################################
    rejected, corrected_p_vals, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    
    # Add the true corrected results back to your summary dataframe
    summary_df['significant_Benjamini-Hochberg_corrected'] = rejected
    summary_df['corrected_p_value'] = corrected_p_vals
    
    
    #####################################################################################
    #Statistical significance only tells you that a difference exists
    #it doesn't tell you if numbers made the headlines better or worse. 
    #need to segment your significant tests to see how often the treatment beat the control.
    ########################################################################################
    
    # Filter down to ONLY your truly significant test records
    significant_tests = summary_df[summary_df['significant_Benjamini-Hochberg_corrected'] == True].drop(columns=["CI_plot"]).copy()
    
    # Classify the direction of the change
    significant_tests['direction'] = 'neutral'
    significant_tests.loc[significant_tests['treatment_ctr'] > significant_tests['control_ctr'], 'direction'] = 'treatment_won'

    # Print results
    print(f"Total valid tests analyzed: {len(summary_df)}")
    print(f"Number of statistically significant tests: {summary_df['significant'].sum()}")
    
    print(f"True Significant Tests (After FDR Correction): {summary_df['significant_Benjamini-Hochberg_corrected'].sum()}")
    
    # Count the distribution
    direction_counts = significant_tests['direction'].value_counts()
    print("\n=== Direction of Significant Effects ===")
    print(direction_counts)
    
    # Calculate the winning percentage
    win_pct = (direction_counts.get('treatment_won', 0) / len(significant_tests)) * 100
    print(f"\nWhen a test was significant, treatment out-performed control {win_pct:.1f}% of the time.")

    # Calculate the relative lift for each significant test
    significant_tests['lift'] = (significant_tests['treatment_ctr'] - significant_tests['control_ctr']) /    significant_tests['control_ctr'] 
    average_lift = significant_tests['lift'].mean() * 100
    print(f"Average relative CTR uplift in winning tests: {average_lift:.1f}%")
    return(summary_df, significant_tests )

def clean_memory():
    # clearn memory
    import gc
    control_group  = None
    treatment_group = None
    summary_df = None
    significant_tests = None
    
    
    #del clic_test_eyecatcher_gt_1
    #del clic_test_eyecatcher_gt_1_all
    #del conf_click_list
    #del eyecatcher_counts
    #del filtered_counts
    #del zero_clicks_mask
    #del df_big
    #del tup
    
    #del master_df  # Delete the temporary chunk dataframe
        
    # Absolute Matplotlib nuke
    plt.clf()
    plt.close('all')
        
    # Run garbage collection twice (to handle cyclic references)
    gc.collect()
    gc.collect()

    for name, obj in list(globals().items()):
        if isinstance(obj, pd.DataFrame):
            mem_mb = obj.memory_usage(deep=True).sum() / 1024**2
            print(f"{name:25s} {obj.shape} {mem_mb:.2f} MB")