from functools import reduce
import logging
import textwrap

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from ai4good.models.abm.abm_model import ABM
from ai4good.models.abm.initialise_parameters import Parameters
from ai4good.webapp.apps import dash_app, facade, model_runner, cache, local_cache, cache_timeout
from ai4good.webapp.abm_model_report_utils import *


@cache.memoize(timeout=cache_timeout)
def layout(camp, profile, cmp_profiles):

    _, profile_df, params, _ = get_model_result(camp, profile)

    return html.Div(
        [
            dcc.Markdown(disclaimer(camp), style={'margin': 30}),
            html.H1(f'AI for Good Simulator Model Report for {camp} Camp {profile} profile', style={'margin': 30}),
            dcc.Markdown(glossary(), style={'margin': 30}),
            dcc.Markdown(overview1(camp, params), style={'margin': 30}),
            html.Img(src='/static/abm_model.png'),
            html.Div(overview_population(params), style={'margin': 30}),
            dcc.Loading(html.Div([], id='main_section_part1', style={'margin': 30})),
            dcc.Loading(html.Div([], id='main_section_part2', style={'margin': 30})),
            base_profile_chart_section(),
            dcc.Loading(html.Div([], id='cmp_section', style={'margin': 30})),
            html.Div(camp, id='_camp_param', style={'display': 'none'}),
            html.Div(profile, id='_profile_param', style={'display': 'none'}),
            html.Div('¬'.join(cmp_profiles), id='_cmp_profiles', style={'display': 'none'})

        ], style={'margin': 50}
    )


def disclaimer(camp):
    return textwrap.dedent(f'''
    ##### Disclaimer: This report is a draft report from AI for Good Simulator on the COVID-19 situation
    in {camp} camp. The insights are preliminary and they are subject to future model
    fixes and improvements on parameter values
    ''').replace('\n', ' ')


def glossary():
    return textwrap.dedent(f'''
    ## 0. Glossary 
    * **hospitalisation/critical care demand person days**: The residents go into the hospitalisation/critical stage signify they require care but they may not receive the care depending on the capacity so this aggregates the hospitalisation/critical demand by person times number of days. If a unit cost of care is known, the total medical expense can be calculated.
    * **IQR (interquartile range)**: The output of modelling are represented as Interquartile range representing a confidence interval of 25%-75%.
    ''')


def overview1(camp: str, params: Parameters):
    return textwrap.dedent(f'''
    ## 1. Overview
    This report provides simulation-based estimates for COVID-19 epidemic scenarios for the {camp} camp. 
    There are an estimated {int(params.population)} people currently living in the camp. 
    We developed the first agent-based model of an epidemic in a displacement camp setting and applied it to evaluate potential interventions to combat the spread of COVID-19. 
    The model tracks individuals as they undertake daily activities in a simulated camp. COVID-19 can be transmitted when infected and susceptible individuals interact. 
    The demographics and spatial structure of the model camp simulate Moria, and the parameters that control COVID-19 transmission rates and disease progression are estimated from the literature. 
    We modelled COVID-19 outbreaks without interventions and in the presence of four interventions feasible for displacement camps: 
    i) sectoring, 
    ii) transmission reduction,
    iii) remove-and-isolate, 
    iv) lockdown. 
    In sectoring, the central food line is eliminated and the camp is divided into sectors. Each sector has its own food line, and each individual uses the food line in the sector in which it lives. Thus, time spent in the food line is reduced and transmission in the food line becomes local rather than global. 
    Transmission reduction could be any policy or behaviour that reduces the probability of transmission when individuals interact (e.g., the use of face masks, frequent hand washing, maintaining safe distances from others). Frequent hand-washing and maintaining safe distances from others are likely to be impossible in Moria, but residents have been provided with face masks.
    Therefore, we simulated face mask use; in remove-and-isolate, households with symptomatic individuals are moved to an isolation facility to prevent onward transmission of the infection. Finally, in lockdown, individuals are constrained to remain within some distance of their homes, except when visiting shared toilets or food lines.
    A small proportion of the population violates the lockdown rule. For each intervention or combination of interventions, we conducted simulations in which we introduced an infected individual into the population, and we recorded the proportion of times that an epidemic occurred (i.e., 20 or more people became infected). 
    If an epidemic occurred, we recorded 
    i) the peak proportion of the population infected, 
    ii) the time from the introduction of the first case until peak infection, 
    iii) the total proportion of the population that became infected. 
    For remove-and-isolate interventions, we also recorded the maximum number of individuals kept in isolation to assess the feasibility of the intervention
    
    GS: FIND MEANINGFUL GRAPH (LIKE pag.7  paper??)
    The graph below represents the disease transition dynamics for each individual included in the modelling studies. 
    The model we use is a deterministic, age-specific compartment model.
    We produce the analysis based on 
    {params.control_dict['numberOfIterations']} simulation runs over a range of possible parameters.
    ''')


def overview_population(params: Parameters):
    # GS: in this section SUMMARY OF POPULATION AND HOUSEHOLD STRUCTURE, i.e. # in isoboxes/tents, #ethnical backgrounds. CAN WE PUT Fig 3 pag 14 from the paper?
    df = params.population_frame.copy()
    df['Population structure'] = df['Population_structure'].map('{:,.1f}%'.format)
    df['Number of residents'] = df['Population_structure'] * params.population / 100.0
    df['Number of residents'] = df['Number of residents'].astype(int)
    df = df[['Age', 'Population structure', 'Number of residents']]

    return [
        dcc.Markdown(textwrap.dedent(f'''
        The ABM model describe the population and the camp:
        * Population specific parameters: population size,age, sex, condition (healty or with pre-existing condition), disease state.
        * Camp specific parameters: each individual is a member of a household that occupies either an isobox or a tent each characterized by a mean occupancy in the camp.The exact occupancy of each isobox or tent is drawn from a Poisson distribution, and
          individuals are assigned to isoboxes or tents randomly without regard to sex or age. The camp covers a 1 x 1 (e.g., km) square (figure 3). Isoboxes are assigned to random
          locations in a central square that covers one half of the area of the camp. Tents are assigned to random locations in the camp outside of the central square. There are 144 toilets evenly
          distributed throughout the camp. Toilets are placed at the centres of the squares that form a 12 x 12 grid covering the camp. The camp has one food line. The position of the food line is
          not explicitly modelled.  
          In Moria, the homes of people with the same ethnic or national background are spatially clustered, and people interact more frequently with others from the same background as
          themselves                
        ''')),
        dbc.Row([
            dbc.Col([
                html.Div(html.B(f'Population breakdown of {params.camp} camp with {int(params.population)} residents')),
                dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
            ], width=4)
        ]),
        dcc.Markdown(textwrap.dedent(f'''
        The parameter values that describe disease progression and transmission are drawn from the literature.If an individual becomes infected, the infection progresses through a series of disease states according to a predefined probability
        '''))
    ]


@local_cache.memoize(timeout=cache_timeout)
def get_model_result(camp: str, profile: str):
    logging.info("Reading data for: " + camp + ", " + profile)
    mr = model_runner.get_result(ABM.ID, profile, camp)
    assert mr is not None
    profile_df = facade.ps.get_params(ABM.ID, profile).drop(columns=['Profile'])
    params = Parameters(facade.ps, camp, profile_df, {})
    report = load_report(mr, params)
    return mr, profile_df, params, report


@dash_app.callback(
    Output('main_section_part1', 'children'),
    [Input('_camp_param', 'children'), Input('_profile_param', 'children')],
)
@cache.memoize(timeout=cache_timeout)
def render_main_section_part1(camp, profile):
    mr, profile_df, params, _ = get_model_result(camp, profile)

    prevalence = mr.get('prevalence_all')
    peak_critical_care_demand = prevalence[prevalence['Outcome'] == 'Critical Care Demand']['Peak Number IQR'].iloc[0]

    prevalence_age = mr.get('prevalence_age').reset_index()
    prevalence_age = prevalence_age.rename(columns={"level_1": "Age"})

    return [
        dcc.Markdown(textwrap.dedent(f'''
         ## 2. Base COVID-19 Epidemic Trajectory for profile "{profile}"

         Following parameters were used during modelling 
         ''')),
        dbc.Row([
            dbc.Col([
                html.Div(html.B(f'{profile} profile details')),
                dbc.Table.from_dataframe(render_profile_df(profile_df, params), bordered=True, hover=True, striped=True),
            ], width=4)
        ]),
        dcc.Markdown(textwrap.dedent(f'''
        Here we assume the epidemic spreads through the camp without any non-pharmaceutical intervention in place and the peak incidence 
        (number of cases), the timing and the cumulative case counts are all presented by interquartile range values (25%-75% quantiles)
        and they respectively represent the optimistic and pessimistic estimates of the spread of the virus given the uncertainty 
        in parameters estimated from epidemiological studies. In the simulations, we explore a range of reproduction numbers, 
        pre-symptomatic duration, rate of recovery, rate of severe infections and death rates based on estimates in the European 
        and Asian settings to nearly what is estimated from a high population density location like a cruise ship. 
        ''')),
        dbc.Row([
            dbc.Col([
                html.Div(html.B(f'Peak day and peak number for prevalences of different disease states of COVID-19')),
                dbc.Table.from_dataframe(prevalence, striped=True, bordered=True, hover=True)
            ], width=4)
        ]),
        dcc.Markdown(textwrap.dedent(f'''
        The death estimate is based on the fact the patients require critical care will receive appropriate treatment from the 
        {params.icu_count} ICU beds that are currently available in {params.camp}. The prevalence of death could be as 
        high as the peak critical care demand ({peak_critical_care_demand}) if camp residents are denied treatment at the 
        ICU facility on the island.  
        ''')),
        dbc.Row([
            dbc.Col([html.Div([
                html.B(f'Peak day and peak prevalences of different disease states of COVID-19 breakdown by age'),
            ])])
        ]),
        dbc.Row([
            dbc.Col([
                html.B(f'Incident Cases'),
                dbc.Table.from_dataframe(
                    prevalence_age[prevalence_age['level_0'] == 'Incident Cases'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4),
            dbc.Col([
                html.B(f'Hospital Demand'),
                dbc.Table.from_dataframe(
                    prevalence_age[prevalence_age['level_0'] == 'Hospital Demand'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4),
            dbc.Col([
                html.B(f'Critical Demand'),
                dbc.Table.from_dataframe(
                    prevalence_age[prevalence_age['level_0'] == 'Critical Demand'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4),
        ])
    ]


def render_profile_df(df, params):
    res = []
    for idx, r in df.iterrows():
        p = r['Parameter']
        s = r['Start Time']
        e = r['End Time']
        v = r['Value']
        dct = {'Parameter': p}

        if s != '<no_edit>' and abs(float(s) - float(e)) < 1E-1:
            value = 'Not active'
        elif p == 'better_hygiene':
            value = f'{params.control_dict["better_hygiene"]["value"]} from day {s} to {e}'
        elif p == 'ICU_capacity':
            value = f'{v} units'
        elif p == 'remove_symptomatic':
            value = f'{v} people/day from day {s} to {e}'
        elif p == 'shielding':
            value = 'Used' if params.control_dict["shielding"]["used"] else 'Not used'
        elif p == 'remove_high_risk':
            value = f'{v} people/day from day {s} to {e} from ' \
                    f'{params.control_dict["remove_high_risk"]["n_categories_removed"]} high risk categories'
        elif p == 't_sim':
            value = f'{v} days'
        else:
            value = None
        if value:
            dct['Value'] = value
            res.append(dct)
    return pd.DataFrame(res)


@dash_app.callback(
    Output('main_section_part2', 'children'),
    [Input('_camp_param', 'children'), Input('_profile_param', 'children')],
)
@cache.memoize(timeout=cache_timeout)
def render_main_section_part2(camp, profile):
    mr, _, params, _ = get_model_result(camp, profile)

    t_sim = params.control_dict['t_sim']

    cumulative_all = mr.get('cumulative_all')
    cumulative_age = mr.get('cumulative_age').reset_index()
    cumulative_age = cumulative_age.rename(columns={"level_1": "Age"})

    return [
        dbc.Row([
            dbc.Col([
                html.B(f'Cumulative case counts of different disease states of COVID-19 spanning {t_sim} days'),
                dbc.Table.from_dataframe(cumulative_all, striped=True, bordered=True, hover=True)
            ], width=4),
        ]),
        dcc.Markdown(textwrap.dedent(f'''Table above show cumulative counts, hospital-person days can be translated into
          projected medical costs or time required from medical staff if the medical cost and time taken is known for 
          treating one patient for a day.''')),

        dbc.Row([
            dbc.Col([html.Div([
                html.B(f'Cumulative case counts of different disease states of COVID-19 breakdown by age'),
            ])])
        ]),
        dbc.Row([
            dbc.Col([
                html.B(f'Symptomatic Cases'),
                dbc.Table.from_dataframe(
                    cumulative_age[cumulative_age['level_0'] == 'Symptomatic Cases'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4),
            dbc.Col([
                html.B(f'Hospital Person-Days'),
                dbc.Table.from_dataframe(
                    cumulative_age[cumulative_age['level_0'] == 'Hospital Person-Days'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4)
        ]),
        dbc.Row([
            dbc.Col([
                html.B(f'Critical Person-days'),
                dbc.Table.from_dataframe(
                    cumulative_age[cumulative_age['level_0'] == 'Critical Person-days'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4),
            dbc.Col([
                html.B(f'Deaths'),
                dbc.Table.from_dataframe(
                    cumulative_age[cumulative_age['level_0'] == 'Deaths'].drop(columns=['level_0']),
                    striped=True, bordered=True, hover=True)
            ], width=4)
        ])
    ]


def base_profile_chart_section():
    options = [
        {'label': 'All ages', 'value': 'ALL'},
        {'label': '<9 years', 'value': '0-9'},
        {'label': '10-19 years', 'value': '10-19'},
        {'label': '20-29 years', 'value': '20-29'},
        {'label': '30-39 years', 'value': '30-39'},
        {'label': '40-49 years', 'value': '40-49'},
        {'label': '50-59 years', 'value': '50-59'},
        {'label': '60-69 years', 'value': '60-69'},
        {'label': '70+ years', 'value': '70+'}
    ]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.B('Plots of changes in symptomatically infected cases, hopitalisation cases, critical care cases '
                       'and death incidents over the course of simulation days'),
                dcc.Dropdown(
                    id='charts_age_dropdown',
                    options=options,
                    value='ALL',
                    clearable=False,
                    style={'margin-top': 5}
                ),
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Loading(html.Div([], id='chart_section_plot_container')),
            ], width=12)
        ])
    ], style={'margin': 30})


@dash_app.callback(
    Output('chart_section_plot_container', 'children'),
    [Input('_camp_param', 'children'), Input('_profile_param', 'children'), Input('charts_age_dropdown', 'value')],
)
def render_main_section_charts(camp, profile, age_to_plot):
    mr, profile_df, params, report = get_model_result(camp, profile)
    logging.info(f"Plotting {age_to_plot}")

    columns_to_plot = ['Infected (symptomatic)', 'Hospitalised', 'Critical', 'Deaths']
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True,
                        vertical_spacing=0.05,
                        horizontal_spacing=0.05,
                        subplot_titles=columns_to_plot)

    for i, col in enumerate(columns_to_plot):
        row_idx = int(i % 2 + 1)
        col_idx = int(i / 2 + 1)
        if age_to_plot != 'ALL':
            age_cols = [c for c in report.columns if (age_to_plot in c) and (c.startswith(col))]
            assert len(age_cols) == 1
            col = age_cols[0]
        p1, p2 = plot_iqr(report, col)
        fig.add_trace(p1, row=row_idx, col=col_idx)
        fig.add_trace(p2, row=row_idx, col=col_idx)
        fig.update_yaxes(title_text=col, row=row_idx, col=col_idx)

    x_title = 'Time, days'
    fig.update_xaxes(title_text=x_title, row=2, col=1)
    fig.update_xaxes(title_text=x_title, row=2, col=2)

    fig.update_traces(mode='lines')
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=800,
        showlegend=False
    )

    return [
        dcc.Graph(
            id='plot_all_fig',
            figure=fig,
            style={'width': '100%'}
        )
    ]


@dash_app.callback(
    Output('cmp_section', 'children'),
    [Input('_camp_param', 'children'), Input('_profile_param', 'children'), Input('_cmp_profiles', 'children')],
)
@cache.memoize(timeout=cache_timeout)
def interventions(camp, profile, cmp_profiles):

    _, base_profile, base_params, base_df = get_model_result(camp, profile)
    profiles = cmp_profiles.split('¬')

    if len(profiles) == 0 or (len(profiles) == 1 and len(profiles[0].strip()) == 0):
        return []

    intervention_content = [intervention(camp, p, i+1, base_df, base_params, base_profile, profile) for i, p in enumerate(profiles)]
    intervention_content = reduce(list.__add__, intervention_content)

    return [
        dcc.Markdown(textwrap.dedent(f'''
        ## 2. Intervention scenarios

        We compare each intervention scenario to baseline. Baseline charts are in blue as before, intervention charts 
        are in red.
         ''')),
        html.Div(intervention_content)
    ]


def intervention(camp, cmp_profile_name, idx, base_df, base_params, base_profile, base_profile_name):
    _, cmp_profile, cmp_params, cmp_df = get_model_result(camp, cmp_profile_name)

    tbl = diff_table(base_df, cmp_df, cmp_params.population)
    profile_diff = profile_diff_tbl(base_profile, base_params, cmp_profile, cmp_params)

    return [
        dcc.Markdown(textwrap.dedent(f'''
        ## 2.{idx} {cmp_profile_name} intervention comparison
        
        Here we compare {cmp_profile_name} model profile with base {base_profile_name} profile explored in the main 
        section. Compared to base profile {cmp_profile_name} has following changes:
        ''')),
        dbc.Row([
            dbc.Col([
                html.B(f'{cmp_profile_name} parameter changes compared to {base_profile_name}'),
                dbc.Table.from_dataframe(profile_diff, bordered=True, hover=True,  striped=True),
            ], width=4)
        ]),
        dcc.Markdown(textwrap.dedent(f'''
        #### Comparison results
        ''')),
        dbc.Row([
            dbc.Col([
                html.B(f'{cmp_profile_name} to {base_profile_name} comparison table'),
                dbc.Table.from_dataframe(tbl, bordered=True, hover=True)
            ], width=4)
        ])
    ] + intervention_plots(base_df, cmp_df, base_profile_name, cmp_profile_name)


def intervention_plots(base_df, cmp_df, base_profile_name, cmp_profile_name):
    columns_to_plot = ['Infected (symptomatic)', 'Hospitalised', 'Critical', 'Deaths']
    fig = make_subplots(rows=2, cols=2, shared_xaxes=True,
                        vertical_spacing=0.05,
                        horizontal_spacing=0.05,
                        subplot_titles=columns_to_plot)

    for i, col in enumerate(columns_to_plot):
        row_idx = int(i % 2 + 1)
        col_idx = int(i / 2 + 1)

        b1, b2 = plot_iqr(base_df, col, ci_name_prefix=f'{base_profile_name} ',
                          estimator_name=f'{base_profile_name} median')
        c1, c2 = plot_iqr(cmp_df, col, ci_name_prefix=f'{cmp_profile_name} ',
                          estimator_name=f'{cmp_profile_name} median', color_scheme=color_scheme_secondary)

        fig.add_trace(b2, row=row_idx, col=col_idx)
        fig.add_trace(c2, row=row_idx, col=col_idx)
        fig.add_trace(b1, row=row_idx, col=col_idx)
        fig.add_trace(c1, row=row_idx, col=col_idx)

        fig.update_yaxes(title_text=col, row=row_idx, col=col_idx)
    x_title = 'Time, days'
    fig.update_xaxes(title_text=x_title, row=2, col=1)
    fig.update_xaxes(title_text=x_title, row=2, col=2)

    fig.update_traces(mode='lines')
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=800,
        showlegend=False
    )

    return [
        dcc.Graph(
            id='intervention_plots_fig',
            figure=fig,
            style={'width': '100%'}
        )
    ]


def profile_diff_tbl(base_profile, base_params, cmp_profile, cmp_params):
    bp = render_profile_df(base_profile, base_params)
    cp = render_profile_df(cmp_profile, cmp_params)

    j = bp.merge(cp, how='left', on='Parameter')

    cmp_result = []
    for index, r in j.iterrows():
        is_eq = r[f'Value_x'] == r[f'Value_y']
        if not is_eq:
            cmp_row = {
                'Parameter': r['Parameter'],
                'Value': f"{r['Value_x']} -> {r['Value_y']}"
            }
            cmp_result.append(cmp_row)
    return pd.DataFrame(cmp_result)


color_scheme_main = ['rgba(0, 176, 246, 0.2)', 'rgba(255, 255, 255,0)', 'rgb(0, 176, 246)']
color_scheme_secondary = ['rgba(245, 186, 186, 0.5)', 'rgba(255, 255, 255,0)', 'rgb(255, 0, 0)']


def plot_iqr(df: pd.DataFrame, y_col: str,
             x_col='Time', estimator=np.median, estimator_name='median', ci_name_prefix='',
             iqr_low=0.25, iqr_high=0.75,
             color_scheme=color_scheme_main):
    grouped = df.groupby(x_col)[y_col]
    est = grouped.agg(estimator)
    cis = pd.DataFrame(np.c_[grouped.quantile(iqr_low), grouped.quantile(iqr_high)], index=est.index,
                       columns=["low", "high"]).stack().reset_index()

    x = est.index.values.tolist()
    x_rev = x[::-1]

    y_upper = cis[cis['level_1'] == 'high'][0].values.tolist()
    y_lower = cis[cis['level_1'] == 'low'][0].values.tolist()
    y_lower = y_lower[::-1]

    p1 = go.Scatter(
        x=x + x_rev, y=y_upper + y_lower, fill='toself', fillcolor=color_scheme[0],
        line_color=color_scheme[1], name=f'{ci_name_prefix}{iqr_low*100}% to {iqr_high*100}% interval')
    p2 = go.Scatter(x=x, y=est, line_color=color_scheme[2], name=f'{y_col} {estimator_name}')
    return p1, p2
