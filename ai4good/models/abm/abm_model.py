from typeguard import typechecked
from ai4good.models.model import Model, ModelResult
from ai4good.params.param_store import ParamStore
from ai4good.models.abm.initialise_parameters import Parameters
# from ai4good.webapp.cm_model_report_utils import *
import logging
from . import abm
import numpy as np
import pandas as pd


@typechecked
class ABM(Model):

    ID = 'agent-based-model'

    def __init__(self, ps: ParamStore):
        Model.__init__(self, ps)

    def id(self) -> str:
        return self.ID

    def result_id(self, p: Parameters) -> str:
        return p.sha1_hash()

    def run(self, p: Parameters) -> ModelResult:
    
        for i in range(p.number_of_steps):
    
            p.track_states[i, :] = np.bincount(self.population[:, 1].astype(int), minlength=14)

            if abm.epidemic_finish(np.concatenate((self.track_states[i, 1:6], self.track_states[i, 7:self.number_of_states])), i):
                return

            if (p.ACTIVATE_INTERVENTION and (i > 0)):
                p.iat1 = i
                p.ACTIVATE_INTERVENTION = False
                p.smaller_movement_radius = 0.001
                p.transmission_reduction = 0.25
                p.foodpoints_location, p.foodpoints_numbers, p.foodpoints_sharing = abm.position_foodline(p.households_location, p.foodline_blocks[0], p.foodline_blocks[1])
                p.local_interaction_space = abm.interaction_neighbours_fast(p.households_location, p.smaller_movement_radius, p.larger_movement_radius, p.overlapping_rages_radius, p.ethnical_corellations)
                p.viol_rate = 0.05  
                p.population[:, 8] = np.where(np.random.rand(p.total_population) < p.viol_rate, 1, 0)

            p.population[np.where(p.population[:, 1] > 0), 3] += 1

            p.population, p.total_number_of_hospitalized = abm.disease_state_update(
                p.population,
                p.mild_rec,
                p.sev_rec,
                p.pick_sick,
                p.total_number_of_hospitalized)

            p.population = abm.assign_new_infections(p.population,
                                                        p.toilets_sharing,
                                                        p.foodpoints_sharing,
                                                        p.num_toilet_visit,
                                                        p.num_toilet_contact,
                                                        p.num_food_visit,
                                                        p.num_food_contact,
                                                        p.pct_food_visit,
                                                        p.transmission_reduction,
                                                        p.local_interaction_space,
                                                        p.probability_infecting_person_in_household_per_day,
                                                        p.probability_infecting_person_in_foodline_per_day,
                                                        p.probability_infecting_person_in_toilet_per_day,
                                                        p.probability_infecting_person_in_moving_per_day)

            p.population = abm.move_hhl_quarantine(p.population, p.probability_spotting_symptoms_per_day)

            p.quarantine_back = np.logical_and(p.population[:, 1] == 13, p.population[:, 3] >= p.clearday)
            p.population[p.quarantine_back, 1] = 6

            # placeholders for the report
            standard_sol = [{'t': range(p.number_of_steps)}]
            perc = [0] * p.number_of_steps
            percentiles = [perc, perc, perc, perc, perc]
            config_dict = []
            [config_dict.append(dict(
                                beta           = 0,
                                latentRate     = 0,
                                removalRate    = 0,
                                hospRate       = 0,
                                deathRateICU   = 0,
                                deathRateNoIcu = 0
                            )) for _ in range(p.number_of_steps)]

        report_raw = [[0]]
        prevalence_age = pd.DataFrame([[0]])
        prevalence_all = pd.DataFrame([[0]])
        cumulative_all = pd.DataFrame([[0]])
        cumulative_age = pd.DataFrame([[0]])

        return ModelResult(self.result_id(p), {
            'standard_sol': standard_sol,
            'percentiles': percentiles,
            'config_dict': config_dict,
            'params': p,
            'report': report_raw,
            'prevalence_age': prevalence_age,
            'prevalence_all': prevalence_all,
            'cumulative_all': cumulative_all,
            'cumulative_age': cumulative_age
        })


