import numpy as np
import plotly.graph_objects as go


def calculate_gini_curve(male_num, female_num, n):
    # Define the function to calculate wealth distribution and plot Lorenz curve
    def compute_lorenz_curve(num_samples, total_wealth, intervals, t_values, label):
        points_in_intervals = []

        # Calculate points in each interval
        for i in range(len(intervals) - 1):
            count = np.sum((t_values >= intervals[i]) & (t_values < intervals[i + 1]))
            points_in_intervals.append(count)

        print(f"Points in each interval ({label}):", points_in_intervals)

        # Calculate wealth distribution
        b = total_wealth / len(points_in_intervals)
        sequence = []
        for count in points_in_intervals:
            if count > 0:
                c = b / count
            else:
                c = 0  # Handle the divide by zero case
                print('warning:you need to extend the number of n')
            sequence.extend([c] * count)

        # Calculate Gini coefficient
        sequence.sort()
        sample_count = len(sequence)
        cw = []
        for i in range(sample_count):
            cw.append(sum(sequence[:i + 1]))

        total_wealth = cw[-1]
        for i in range(len(cw)):
            cw[i] = cw[i] / total_wealth
        cw = [0] + cw
        cp = [0] + [i / sample_count for i in range(1, sample_count + 1)]
        B = 0
        for i in range(1, sample_count + 1):
            B = B + (cw[i] + cw[i - 1]) * (cp[i] - cp[i - 1]) / 2
        A = 0.5 - B
        gini_coefficient = A / (A + B)

        # Find the middle index for labeling
        middle_index = len(cp) // 2

        # Plot Lorenz curve
        fig.add_trace(go.Scatter(x=cp, y=cw, mode='lines', name=f'{label} Lorenz Curve', line=dict(dash='dash')))
        fig.add_trace(go.Scatter(x=[cp[middle_index]], y=[cw[middle_index]], mode='markers',
                                 marker=dict(size=10), name=f'{label} Middle Point'))

        return gini_coefficient, points_in_intervals, sequence

    # Create a plot object
    fig = go.Figure()

    # Adding line of equality
    cp = np.linspace(0, 1, 100)
    fig.add_trace(go.Scatter(x=cp, y=cp, mode='lines', name='Line of Equality', line=dict(color='red')))

    # Male-specific computation
    male_intervals = [2 ** i * np.pi for i in range(2, 3 + n)]
    male_t_values = np.linspace(male_intervals[0], male_intervals[-1], male_num + 1)
    male_gini_coefficient, male_points_intervals, male_sequence = compute_lorenz_curve(
        male_num, total_wealth, male_intervals, male_t_values, 'Male'
    )
    print(male_intervals)

    # Female-specific computation
    female_intervals = [2 * np.pi]
    for i in range(1, n + 1):
        next_interval = female_intervals[-1] + (2 * i - 1) * 2 * np.pi
        female_intervals.append(next_interval)
    female_t_values = np.linspace(2 * np.pi, female_intervals[-1], female_num + 1)
    female_gini_coefficient, female_points_intervals, female_sequence = compute_lorenz_curve(
        female_num, total_wealth, female_intervals, female_t_values, 'Female'
    )
    print(female_intervals)

    # Define the title with all required information
    title_text = (
        f"Male Gini Coefficient: {male_gini_coefficient:.3f}<br>"
        f"Female Gini Coefficient: {female_gini_coefficient:.3f}<br>"
        f"Male Points in Intervals: {male_points_intervals}<br>"
        f"Female Points in Intervals: {female_points_intervals}"
    )

    # Update layout settings
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor='center', font=dict(size=14)),
        xaxis_title='Population Percentage',
        yaxis_title='Wealth Percentage',
        xaxis=dict(tickformat=',.0%', range=[0, 1]),
        yaxis=dict(tickformat=',.0%', range=[0, 1]),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    # Show the plot
    fig.show()


# Set parameters
male_num=950
female_num=950
total_wealth=330750
n = 3  # Number of intervals 建议在10以内

# Calculate and plot Gini curves
calculate_gini_curve(male_num, female_num, n)
