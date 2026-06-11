#basics
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# stats
from scipy.stats import chisquare
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
from scipy.stats import dunnett
from statsmodels.stats.proportion import proportion_confint

#others
import math
import os
from pathlib import Path
from IPython.display import HTML, display
import ipywidgets as widgets
import pickle

def traffic_plot(df,test_id):
    """
    This makes  plot of the traffic share. The impression of an arm in experiment over the total impressions of the experiemnt
    Takes a dataframe
    Returns a link of the plot
    """
    output_dir = "traffic_share_plots"
    os.makedirs(output_dir, exist_ok=True)

    ax = df.sort_values("traffic_share", ascending=False).plot(x="eyecatcher_id", y="traffic_share", kind="bar", title=f"Test {test_id}")

    file_name = f"traffic_share_{test_id}.png"
    file_path = os.path.join(output_dir, file_name)
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()  # Prevents plot from popping up now

    # Convert the file path into a clickable HTML link string
    # target="_blank" makes it open in a new browser tab when clicked
    return f'<a href="{file_path}" target="_blank">View Plot</a>'


def chi_square(df,alpha):
    """
    This runs the chi square to check that the samples from each arm come from the same distribution.
    Together with the traffic plot, it verifies the  randomization meachanism When the Chi-Square test returns a statistically significant p-value ($p < \alpha$), it indicates that the actual distribution of users/impressions across your variants deviates significantly from what was intended.
    If you ignore a significant SRM and proceed to a Z-proportion test for CTR, your results will likely be invalid and misleading for two main reasons:
    ** selection bias
    ** Loss of internal validity: any observed lift or drop in your CTR Z-test could simply be an artifact of this assignment imbalance rather than the actual performance of the headline or eyecatcher.
    Take a dataframe and alpha
    return the result of the hypothesis test
    """
       
    #Group by arm to ensure exact alignment and sum the impressions
    arm_counts = df.groupby("eyecatcher_id")["impressions"].sum()
    
    # number of arms
    #nums_arm=len(df["eyecatcher_id"])
    nums_arm = len(arm_counts)
    
    # make obersved number of impressions for chi test
    #observed=df["impressions"].unique().tolist()
    observed = arm_counts.tolist()
    
    # make total impressions chi test. remember you need to divide by the number of arm
    total_impressions=df["impressions"].sum()
    expected = [total_impressions/nums_arm]*nums_arm
    
    # run chisquare
    chi2_stat, p_value = chisquare(f_obs=observed, f_exp=expected)
    
    # 3. Print the results
    #print(f"Chi-Square Statistic : {chi2_stat:.3f}")
    #print(f"P-value              : {p_value:.3e}")

    # 4. Evaluate significance
    if p_value < alpha:
        return (("Statistically significant. Reject null. At least one group differs."), chi2_stat, p_value)
    else:
        return (("Not statistically significant. Fail to reject null."), chi2_stat, p_value)

def relative_lift_cohen_d(df):
    """
    This caculates  absolute_lift_vs_control, relative_lift_vs_control and cohens_h_vs_control_eff_size
    Because I just want a summary for each experiment, I will only return the max lift and the max cohen d. Also I will return the df
    relative_lift_vs_control: how much each variant is better than the control relatively
    cohens_h_vs_control_eff_size: measure of the size of the effect btw two proportions.
    """
    control_ctr = df["CTR"].min()

    safe_control_ctr = control_ctr if control_ctr > 0 else 1e-9
    
    df["absolute_lift_vs_control"] = df["CTR"] - control_ctr
    
    
    df["relative_lift_vs_control"] = ( df["CTR"] - control_ctr) / safe_control_ctr
    
    #df["cohens_h_vs_control_eff_size"] = df["CTR"].apply( lambda p: proportion_effectsize(p, control_ctr))
    
    if control_ctr == 0:
    # If control is 0, Cohen's h is technically mathematically unstable
        df["cohens_h_vs_control_eff_size"] = 0.0  #
    else:
        df["cohens_h_vs_control_eff_size"] = df["CTR"].apply(lambda p: proportion_effectsize(p, control_ctr))
    
    df.sort_values(by='relative_lift_vs_control', ascending=True, inplace=True)

    max_relative_lift_vs_control=df["relative_lift_vs_control"].max()
    max_cohens_h_vs_control_eff_size=df["cohens_h_vs_control_eff_size"].max()
    
    return (df,max_relative_lift_vs_control,max_cohens_h_vs_control_eff_size)


def power_plot(df,alpha,test_id):
    """
    This is a power plot that shows the effect of the effect size ont the power of the test
    """
    #control_ctr=df["CTR"].min()   # control 0 lift
    control_ctr=df["CTR"].iloc[0]   # control 0 lift
    
    minimum_detectable_lift = df["relative_lift_vs_control"].max()   #  using the max of the data to get the uplift to get to.


    if control_ctr <= 0 or pd.isna(control_ctr) or pd.isna(minimum_detectable_lift):
        print(f"Skipping power plot for {test_id}: Control CTR is 0 or invalid.")
        return f'<span style="color: red;">No Plot Available (Control CTR is 0)</span>'


        
    
    p_variant_target = control_ctr * (1 + minimum_detectable_lift)

    #DEFENSIVE CHECK: Handle mathematically impossible combinations
    #if pd.isna(p_variant_target) or pd.isna(control_ctr) or p_variant_target == control_ctr:
        # Fallback to an incredibly small effect size instead of 0 or NaN to prevent script crashes
       # effect_size = 0.0001
    #else:
        #effect_size = proportion_effectsize(p_variant_target, control_ctr)
    
    effect_size = proportion_effectsize(p_variant_target, control_ctr)
    #print(f"effect_size is {effect_size}")
    
    
    power_analysis = NormalIndPower()
    
    required_n_per_group = power_analysis.solve_power(
        effect_size=effect_size,
        power=0.80,
        alpha=alpha,
        ratio=1,
        alternative="larger"
    )
    #print(f"required_n_per_group is {required_n_per_group}")
    
    # Specify parameters for power analysis
    output_dir = "power_plots"
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 7))
    sample_sizes = np.array(range(10, 50000))
    effect_sizes = np.array([0.001, effect_size, 0.1])
    
    power_analysis.plot_power(nobs=sample_sizes, effect_size=effect_sizes, alternative="larger", alpha=alpha, ratio=1, ax=ax)
    
    # Reference lines
    plt.axvline(x=required_n_per_group, color="purple", linestyle=":")
    #plt.text(required_n_per_group + 200, 0.5, f"Required N ({int(required_n_per_group)})", color="purple")
    #plt.text(required_n_per_group + 200, 0.5, f"Required N ({required_n_per_group:.0f})", color="purple")
    n_scalar = required_n_per_group.item() if hasattr(required_n_per_group, "item") else required_n_per_group
    plt.text(n_scalar + 200, 0.5, f"Required N ({n_scalar:.0f})", color="purple")
    
    actual_per_group = df["impressions"].max()
    plt.axvline(x=actual_per_group, color="black", linestyle=":")
    plt.text(actual_per_group + 200, 0.3, f"Actual N ({int(actual_per_group)})", color="black")
    
    file_name = f"power_plots_{test_id}.png"
    file_path = os.path.join(output_dir, file_name)
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()  # Prevents plot from popping up now

    # Convert the file path into a clickable HTML link string
    # target="_blank" makes it open in a new browser tab when clicked
    return f'<a href="{file_path}" target="_blank">View Plot</a>'


def Dunnett_Hypothesis_test(df,alpha,alpha_significant_str):
    """
    This is the Dunnett_Hypothesis_test. It test every variant vs control. It is more powerful than broad methods (like Bonferroni) because it only tests specific pairs (Treatment vs. Control) rather than every possible     combination. The treatement group is not compared to each other, only to        control. The test test if the variant is greater than the control alternative="greater"
    It returns a dataframe table that shows, Dunnett Statistic, adjusted p-value and the confident interval
    It takes in a dataframe, alpha and alpha_significant_str. This is just a string to make the column so that when alpha changes the alpha_significant_str  change too
    """
    #Isolate control and variant rows
    control_row = df.loc[df["absolute_lift_vs_control"].idxmin()]
    #variants_df = df_confirmatory_exp[df_confirmatory_exp["absolute_lift_vs_control"] != 0].copy()
    variants_df = df.copy()  # I added the control here as variant. So variants_df has everything.
    
    #Reconstruct raw binary arrays (1 for click, 0 for no click)
    # Dunnett's test requires the underlying distributions to compute variance
    def reconstruct_observations(clicks, total_impressions):
        clicks = int(clicks)
        no_clicks = int(total_impressions - clicks)
        return np.concatenate([np.ones(clicks), np.zeros(no_clicks)])
    
    control_obs = reconstruct_observations(control_row["clicks"].item(), control_row["impressions"].item())
    
    variant_samples = []
    variant_id = []
    
    for idx, row in variants_df.iterrows():
        obs = reconstruct_observations(row["clicks"], row["impressions"])
        variant_samples.append(obs)
        variant_id.append(row["eyecatcher_id"])
        
    
    #Execute Dunnett's Test
    # We unpack the variant arrays. alternative='greater' looks for Variant > Control.
    res = dunnett(*variant_samples, control=control_obs, alternative="greater")
    
    #Extract and format the results
    results = []
    for i, eyecatcher__id in enumerate(variant_id):
        # Dunnett's test summary outputs statistics in order of passed variants
        statistic = res.statistic[i]
        p_value = res.pvalue[i]
        
        # Extract corresponding data row for reporting
        v_row = variants_df[variants_df["eyecatcher_id"] == eyecatcher__id].iloc[0]
        
        results.append({
            "Variant (eyecatcher_id)": eyecatcher__id,
            "Variant CTR %": round(v_row['CTR']*100,3),
            "Relative Lift %": round(v_row['relative_lift_vs_control']*100,3),
            "Dunnett Statistic": round(statistic, 3),
            "Adjusted p-value": round(p_value,3),
            alpha_significant_str: "YES" if p_value < alpha else "NO"
        })
     # put result in dataframe
    df_dunnett_results = pd.DataFrame(results)
    
    # for CI calculation
    results_with_ci=[]
    for idx, row in df.iterrows():
        clicks = int(row["clicks"])
        impressions = int(row["impressions"])
        
        # Calculate the 95% confidence interval (alpha=0.05)
        # The 'normal' method uses the standard Wald interval, 
        # but 'wilson' or 'agresti-coull' are great alternative methods for low proportions.
        ci_lower, ci_upper = proportion_confint(count=clicks, nobs=impressions, alpha=alpha, method='wilson')
        
        results_with_ci.append({
            "Variant (eyecatcher_id)": row["eyecatcher_id"],
            "Is Control?": "YES" if row["absolute_lift_vs_control"] == 0 else "NO",
            "CI Lower Bound %": round(ci_lower*100,3),
            "CI Upper Bound %": round(ci_upper*100,3)
        })
    # Convert to DataFrame for a clean view
    df_ci_summary = pd.DataFrame(results_with_ci)
    
    # merge the two columns
    df_final_result= pd.merge(df_dunnett_results, df_ci_summary, left_index=True, right_index=True)
    # clean up
    df_final_result.rename(columns={'Variant (eyecatcher_id)_x': 'Variant (eyecatcher_id)'}, inplace=True)
    df_final_result = df_final_result.drop(columns=["Variant (eyecatcher_id)_y"], errors="ignore")
    
    return (df_final_result)



def confidence_interval_plot(hypo_result_df, alpha,alpha_significant_str,test_id):
    """
    This is just a plot for the confidence interval. It takes a hypo_result_df and alpha and returns a link to view the plots
    """
    # Calculate the directional error bar lengths
    hypo_result_df['error_left'] = np.abs(hypo_result_df['Variant CTR %'] - hypo_result_df['CI Lower Bound %'])
    hypo_result_df['error_right'] = np.abs(hypo_result_df['CI Upper Bound %'] - hypo_result_df['Variant CTR %'])
    #display(hypo_result_df)
    
    # Sort dataframe by CTR so the best performing headlines naturally rise to the top
    hypo_result_df = hypo_result_df.sort_values(by='Variant CTR %', ascending=True).reset_index(drop=True)

    # Specify parameters for CI plots
    output_dir = "confidence_interval_plot"
    os.makedirs(output_dir, exist_ok=True)
    
    #Apply a clean design style
    sns.set_theme(style="whitegrid")
    plt.rc('font', family='sans-serif', size=11)
    
    # Initialize the plot 
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Use distinct coloring to clearly isolate the Control group from the Variants
    colors = [
        'black' if row["Is Control?"] == "YES" else
        'pink' if row[alpha_significant_str] == "YES" else
        #'#4A90E2' if row['Relative Lift %'] != 0 else
        '#4A90E2' for _, row in hypo_result_df.iterrows()]
    
    #Plot points and confidence intervals
    for i, row in hypo_result_df.iterrows():
        ax.errorbar(x=row['Variant CTR %'], y=i, xerr=[[row['error_left']], [row['error_right']]], fmt='o', color=colors[i], markersize=8, capsize=5,  capthick=1.5, linewidth=2,label='Variants' if row['Relative Lift %'] != 0 else 'Control')
         # Add inline text descriptions showing exact performance numbers
        if row['Relative Lift %'] != 0:
            label_text = f"{row['Variant CTR %']:.3f}% (+{row['Relative Lift %']:.1f}%)"
        else:
            label_text = f"{row['Variant CTR %']:.3f}% (Control)"
            
        ax.text(row['CI Upper Bound %'] + 0.03, i, label_text, va='center', fontsize=10, fontweight='bold' if row['Relative Lift %'] == 0 else 'normal')
    
    # Clean up y-labels to combine and backend ID
    y_labels = [f"{row['Variant (eyecatcher_id)']}" for _, row in hypo_result_df.iterrows()]
    ax.set_yticks(range(len(hypo_result_df)))
    ax.set_yticklabels(y_labels, fontsize=10)
    
    #Draw a vertical reference line for the Control Baseline
    control_ctr = hypo_result_df[hypo_result_df['Relative Lift %'] == 0]['Variant CTR %'].values[0]
    ax.axvline(x=control_ctr, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.5, label='Control Baseline') # this alpha is to control the color
    
    # Formatting Labels, Limits, and Titles
    ax.set_title(f"A/B Test Results: Click-Through Rate (CTR) with {(1-alpha)*100}% Confidence Intervals", fontsize=14, pad=15, fontweight='bold')
    ax.set_xlabel("Click-Through Rate (%)", fontsize=12, labelpad=10)
    ax.set_ylabel("Variants", fontsize=12, labelpad=10)
    ax.set_xlim(hypo_result_df['CI Lower Bound %'].min() - 0.1, hypo_result_df['CI Upper Bound %'].max() + 0.4)
    
    # ==========================================
    # UPDATED LEGEND HANDLING (CUSTOM HANDLES)
    # ==========================================
    legend_elements = [
        Line2D([0], [0], marker='o', color='black', label='Control', markersize=8, linestyle='None'),
        Line2D([0], [0], marker='o', color='#4A90E2', label='Variant (Not Significant)', markersize=8, linestyle='None'),
        Line2D([0], [0], marker='o', color='pink', label=alpha_significant_str, markersize=8, linestyle='None'),
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