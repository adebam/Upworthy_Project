# Upworthy A/B Testing Project 

## Part 3: Analysis of All experiments
> <font color="red">[!CAUTION]<br>
> **This notebook can take a while to run, and you can run out of memory.**</font>
> 
> To speed up the calculation and prevent memory issues, go to `/src/helper_functions_2.py` and find the function:<br>
> `def Run_Individual_Proportion_Z_Test(df_all, alpha, variable_to_test):`
> 
> Inside this function, change the following line:<br>
> `plot_CI = confidence_interval_plot(p_val,control_ctr,treatment_ctr,control_lower,control_upper,treatment_lower,treatment_upper,alpha,alpha_significant_str,test_id)`
> 
> to:
> `plot_CI = None`
> 
> This prevents the confidence interval plot from being generated for every test, significantly speeding up the calculation.


In part 3, I want to answer the following: 
1. **Do headlines containing numbers perform better than those without?**
2. **Does framing a headline as a question increase engagement?**
3. **Are shorter headlines more effective than longer ones?**

## Do headlines containing numbers perform better than those without?
Solutions to any of the questions above can be formulated in two ways. A Global Two-proportion Z-test and an individual Two-proportion Z-test for each clickability_id.

#### Global Two-proportion Z-test
In this workflow, the dataset is split into 2 catergories as per whether the headline has a question? or not regardless of the clickability_id. The workflow from Part 1 was followed. The only difference from Part 1 is the hypothesis testing. Overhere, we have a classic A/B test since we are comparing control group (those without numbers) to the treatment (those with). It is set up as follows: 


>    
   **The Null Hypothesis ($H_0$)**: There is **no difference** in performance between headlines containing numbers and headlines without numbers.<br>
   **The Alternative Hypothesis ($H_1$)**: There is a **difference** in performance between headlines containing numbers and headlines without numbers. <br>


In this case, it is a two-sided test as we don't care about the direction of the difference. We only care that there is a difference. This is illustrated in the code below:

```python
# 3. Execute the Two-Proportion Z-Test
z_stat, p_value = proportions_ztest(count, nobs, alternative='two-sided')

# calc CI
control_lower, control_upper = proportion_confint(count=total_control_clicks, nobs=total_control_impressions, alpha=alpha, method='wilson')
#Treatment CTR Confidence Interval
treatment_lower, treatment_upper = proportion_confint(count=total_treatment_clicks, nobs=total_treatment_impressions,  alpha=alpha, method='wilson')
```

Also the test changed from Dunnett's to the common proportions_ztest. The results for the Global Two-proportion Z-test:
```shell
=== Global Two-Proportion Z-Test ===
Treatment CTR: 0.01424
Control CTR: 0.01377
Z-statistic: 35.3732
P-value: 4.4110e-274
Result: Statistically Significant! Reject the null hypothesis.
```
#### Individual Two-proportion Z-test for each clickability_id.
Because headline variations are built to compete inside distinct tests, a global test can sometimes mask localized behavior. This approach runs a distinct proportion Z-test for every single clickability_test_id and tracks which experiments were true winners. The new procedure is as follows:
1. Find all experiments where there are numbers in the headline, also the same experiment should have other headlines that don't have numbers. In the datasets there are 5158 tests like this.
2. Perform the proportion Z-test for each experiment and catalogue whether it is significant or not.
3. **Apply The Benjamini-Hochberg correction** When there are 5158 separate tests, some of the "significant" findings are guaranteed to be false alarms (false negative).The Benjamini-Hochberg procedure (multipletests) is used to control the false discovery rate at 5%.
4. **Determine the Winner** Statistical significance only tells that there is a difference exists—it doesn't tell if numbers made the headlines better or worse ( this is because it is a two-sided test!). Segmentation of the significant tests is necessary to see how often the treatment beat (or lose to) the control.
5. **Calculate the relative lift for each significant test**: How much more the treatment is better (or worse) can be calculated to have a single number to quantify the effects of all the tests.
 The steps above is coded, and the results is displayed below:

```shell
Total valid tests analyzed: 5158
Number of statistically significant tests: 1844
True Significant Tests (After FDR Correction): 1253

=== Direction of Significant Effects ===
direction
treatment_won    806
neutral          447
Name: count, dtype: int64

When a test was significant, treatment out-performed control 64.3% of the time.
Average relative CTR uplift in winning tests: 46.9%
```
The global z-test says that there is a difference between headline with numbers compared to those without. The individual z-test tells us the direction of that difference, ie the treatment is better than the control. 


## Does framing a headline as a question increase engagement?

>    
   **The Null Hypothesis ($H_0$)**: There is **no difference** in performance between headlines containing questions mark and headlines without question mark.<br>
   **The Alternative Hypothesis ($H_1$)**: There is a **difference** in performance between headlines containing questions mark and headlines without question mark. <br>
>

To answer this questions, the variable_to_test in the code can be changed from "any_number" to
"any_questions" for question 2. "any_questions" is a boolean column that is "zero" when there is no question in the headline, and "1" otherwise.
```python
summary_df, significant_tests=Run_Individual_Proportion_Z_Test(df_all, alpha=0.05,  variable_to_test="any_questions")

# 4. Format the master table AND render the HTML strings as raw HTML
styled_master = summary_df.style.format({
    "control_ctr": "{:.3g}", 
    "treatment_ctr": "{:.3g}",
    "p_value": "{:.3g}",
    "corrected_p_value": "{:.3g}",
    "plot_link": lambda x: x
})
# 5. Display the final integrated dataframe
display(styled_master)
display(significant_tests)
```
#### Global Two-proportion Z-test
The result of the global test is as follows

```shell
=== Global Two-Proportion Z-Test ===
Treatment CTR: 0.01234
Control CTR: 0.01412
Z-statistic: -120.9390
P-value: 0.0000e+00
Result: Statistically Significant! Reject the null hypothesis.
```
#### Individual Two-proportion Z-test for each clickability_id.
```shell
Total valid tests analyzed: 6770
Number of statistically significant tests: 2308
True Significant Tests (After FDR Correction): 1519

=== Direction of Significant Effects ===
direction
neutral          1051
treatment_won     468
Name: count, dtype: int64

When a test was significant, treatment out-performed control 30.8% of the time.
Average relative CTR uplift in winning tests: -6.5%
```
Global Two-proportion Z-test tells us the results are significant, but it doesn't tell us why. Individual Two-proportion Z-test for each clickability_id tells us the direction of the significance-- framing the headline as a question reduces clicks. 

## Are shorter headlines more effective than longer ones?
>    
   **The Null Hypothesis ($H_0$)**: There is **no difference** in performance between shorter headlines and longer headlines.<br>
   **The Alternative Hypothesis ($H_1$)**: There is a **difference** in performance between shorter headlines and longer ones.<br>
>

Again, the variable_to_test in the code can be changed to "headline_word_count_gt_mean" for question 3. headline_word_count_gt_mean is a boolean that takes "0" when the current headline character count is less than the mean of the experiment, and "1" otherwise.
```python
summary_df, significant_tests=Run_Individual_Proportion_Z_Test(df_all, alpha=0.05,  variable_to_test="headline_word_count_gt_mean")

# 4. Format the master table AND render the HTML strings as raw HTML
styled_master = summary_df.style.format({
    "control_ctr": "{:.3g}", 
    "treatment_ctr": "{:.3g}",
    "p_value": "{:.3g}",
    "corrected_p_value": "{:.3g}",
    "plot_link": lambda x: x
})
# 5. Display the final integrated dataframe
display(styled_master)
display(significant_tests)
```

#### Global Two-proportion Z-test
```shell
=== Global Two-Proportion Z-Test ===
Treatment CTR: 0.01443
Control CTR: 0.01215
Z-statistic: 187.8254
P-value: 0.0000e+00
Result: Statistically Significant! Reject the null hypothesis.
```
The result of the global test tells us there is a significant difference between shorter headlines compared to longer ones, but we don't know which is better!

#### Individual Two-proportion Z-test for each clickability_id
```shell
Total valid tests analyzed: 15696
Number of statistically significant tests: 4891
True Significant Tests (After FDR Correction): 2945

=== Direction of Significant Effects ===
direction
treatment_won    1727
neutral          1218
Name: count, dtype: int64

When a test was significant, treatment out-performed control 58.6% of the time.
Average relative CTR uplift in winning tests: 40.9%
```
The Individual Two-proportion Z-test for each clickability_id on the other hand, tells us that longer headlines are better than shorter one twice the time.


## Conclusions
Before doing all these analysis, my personal thoughts were that having numbers, question marks and shorter headlines are better for clicks.Analyzing the data showed otherwise!

On the technical side, the framing of the hypothesis statement is very important. Framing the alternative hypothesis as "is treatment better than control" changes the setup of the analysis from a two-sided test to a "larger" test. Obviously, if the  null hypothesis has been set up this way, the treatment will always win 100% of the time!
