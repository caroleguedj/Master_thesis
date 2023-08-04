import mne
import numpy as np
import pandas as pd

def sort_epochs(epochs : mne.Epochs):
    ''' Takes the epochs object and returns a list of epochs objects sorted by condition.

    Parameters
    ----------
    epochs : mne.Epochs
        The epochs object to be sorted.
        the order of the epochs is as follows: 
        'dis_top/target_l': 1,
        'dis_top/target_r': 2,
        'no_dis/target_l': 3,
        'no_dis/target_r': 4,
        'dis_bot/target_l': 5,
        'dis_bot/target_r': 6,
        'dis_right/target_l': 7,
        'dis_left/target_r': 8
    
    Returns
    -------
    sorted_epochs : list of mne.Epochs
        A list of epochs sorted by condition. The order of the epochs is as follows:
        ['no_dis/target_l',
        'no_dis/target_r',
        'dis_right/target_l',
        'dis_left/target_r',
        'dis_mid/target_l',
        'dis_mid/target_r']
    '''
    event_ids = epochs.event_id
    
    sorted_epochs = []
    
    for event in event_ids.keys():
        
        condition = epochs[event]
        sorted_epochs.append(condition)

    # concatenate the the files when the target is on the same side but the distractor is bot or top
    
    dis_vert_target_l = mne.concatenate_epochs([sorted_epochs[0], sorted_epochs[4]])
    dis_vert_target_r = mne.concatenate_epochs([sorted_epochs[1], sorted_epochs[5]])
    
    sorted_epochs.append(dis_vert_target_l)
    sorted_epochs.append(dis_vert_target_r)
    
    # remove useless files
    
    indices_to_remove = [0, 1, 4, 5]
    
    # reverse to avoid index shifting issues
    
    indices_to_remove.sort(reverse=True)
    for index in indices_to_remove:
        del sorted_epochs[index]
    
    return sorted_epochs  



def compute_alpha_by_side(sorted_epochs : list):
    ''' Takes a list of epochs objects sorted by conditions and returns 2 lists of alpha band mean power values (8-12Hz), one for each side of the head.

    Parameters
    ----------
    sorted_epochs : list of mne.Epochs
        a list of epochs objects sorted by condition. The order of the epochs is as follows:
        'no_dis/target_l',
        'no_dis/target_r',
        'dis_right/target_l',
        'dis_left/target_r',
        'dis_mid/target_l',
        'dis_mid/target_r'

    Returns
    -------
    right_power_list : list of float
        a list of alpha band mean power values (8-12Hz) for the right side of the head for each epochs object in sorted_epochs (condition)

    left_power_list : list of float
        a list of alpha band mean power values (8-12Hz) for the left side of the head for each epochs object in sorted_epochs (condition)
    '''
    freqs = np.arange(8, 13)
    right_elecs=[ 'P8', 'P10', 'PO8']
    left_elecs=['P7', 'P9', 'PO7']

    n_cycles = freqs / 2.
    time_bandwidth = 4.
    baseline = None  # no baseline correction
    n_jobs = 1  # number of parallel jobs to run
    
    right_power_list = []
    left_power_list = []

    # compute alpha power and append it to right/left_power_list
    for i in range(len(sorted_epochs)):
        right_power = mne.time_frequency.tfr_morlet(sorted_epochs[i], freqs=freqs, n_cycles=n_cycles, picks=right_elecs,
                                                use_fft=True, return_itc=False, decim=1,
                                                n_jobs=n_jobs, verbose=True)
        right_power_mean = right_power.to_data_frame()[right_elecs].mean(axis=1).mean(axis=0)
        right_power_list.append(right_power_mean)

        left_power= mne.time_frequency.tfr_morlet(sorted_epochs[i], freqs=freqs, n_cycles=n_cycles, picks=left_elecs,
                                                use_fft=True, return_itc=False, decim=1,
                                                n_jobs=n_jobs, verbose=True)
        left_power_mean = left_power.to_data_frame()[left_elecs].mean(axis=1).mean(axis=0)
        left_power_list.append(left_power_mean)
    
    return right_power_list, left_power_list


def extract_conditions(epochs_list : list):
    ''' Takes a list of epochs objects and returns a list of strings containing the conditions.
    
    Parameters
    ----------
    epochs_list : list of mne.Epochs
        a list of epochs objects sorted by condition. 
    
    Returns
    -------
    conditions : list of str
        a list of strings containing the conditions.
    '''
    conditions = []

    for i in epochs_list:

        cond = list(i.event_id.keys())
        conditions.append(cond[0])
    
    return conditions

def alpha_power_df(conditions : list, right_power_list: list, left_power_list : list):
    ''' Takes a list of conditions, a list of alpha power values for the right side of the head and a list of alpha power values for the left side of the head and 
        returns a dataframe containing the conditions, the target side, the distractor side, the alpha side relative to the target and the mean alpha power.

    Parameters
    ----------
    conditions : list of str
        a list of strings containing the conditions.

    right_power_list : list of float
        a list of alpha band mean power values (8-12Hz) for the right side of the head for each epochs object in sorted_epochs (condition)
    
    left_power_list : list of float
        a list of alpha band mean power values (8-12Hz) for the left side of the head for each epochs object in sorted_epochs (condition)

    Returns
    -------
    df : pandas dataframe
        a dataframe containing the conditions, the target side, the distractor side, the side of recording relative to the target (ipsi or contralateral) and the mean alpha power value.
    '''
    df = pd.DataFrame(columns=[['condition','target_side', 'distractor_side', 'alpha_side', 'alpha_power']])
    
    df['condition'] = conditions * 2
    
    df ['alpha_power'] = right_power_list + left_power_list
    
    for row_number in range(len(df)):
                     
                        # add target side
                        if 'target_l' in df.iloc[row_number, 0]:
                            df.iloc[row_number, 1] = 'left'
                        elif 'target_r' in df.iloc[row_number, 0]:
                            df.iloc[row_number, 1] = 'right'
                        
                        # add distractor side
                        if 'dis_top' in df.iloc[row_number, 0] or 'no_dis' in df.iloc[row_number, 0]:
                            df.iloc[row_number, 2] = 'nodis'
                        elif 'dis_right' in df.iloc[row_number, 0]:
                            df.iloc[row_number, 2] = 'right'
                        elif 'dis_left' in df.iloc[row_number, 0]:
                            df.iloc[row_number, 2] = 'left'

                        # add alpha side
                        if row_number <= 5:
                            if 'target_l' in df.iloc[row_number, 0]:
                                df.iloc[row_number, 3] = 'contra'
                            elif 'target_r' in df.iloc[row_number, 0]:
                                df.iloc[row_number,3] = 'ipsi'
                        else:
                            if 'target_l' in df.iloc[row_number, 0]:
                                df.iloc[row_number,3] = 'ipsi'
                            elif 'target_r' in df.iloc[row_number, 0]:
                                df.iloc[row_number,3] = 'contra'
                        
    return df