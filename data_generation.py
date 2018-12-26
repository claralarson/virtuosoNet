from __future__ import division
import pickle
import random
import xml_matching
import copy
import pandas
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--regression', default=True, type=lambda x: (str(x).lower() == 'true'))

args = parser.parse_args()


NUM_TRILL_PARAM = 5
NUM_NORMALIZE_FEATURE = [9, 15, 15]
REGRESSION = args.regression
print('Data type is regression: ', args.regression)

def save_features_as_vector(dataset, num_train, save_name):

    complete_xy = []
    num_total_datapoint = 0
    total_notes = 0
    num_piece = 0
    num_perform = 0
    for piece in dataset:
        num_piece += 1
        for perform in piece:
            num_perform +=1
            train_x = []
            train_y = []
            previous_y = []
            align_matched_status = []
            # is_beat_list = []
            # beat_numbers = []
            # measure_numbers = []
            # voice_numbers = []
            note_locations = []
            prev_feat = [0] * (NUM_NORMALIZE_FEATURE[1] + NUM_TRILL_PARAM)
            features = perform['features']
            score = perform['score']
            composer_vec = perform['composer']
            score_graph = perform['graph']

            for feature in features:
                total_notes += 1
                if not feature.qpm == None:
                    # train_x.append(
                    #     [feature.pitch_interval, feature.duration,
                    #      feature.duration_ratio, feature.beat_position, feature.measure_length,
                    #      feature.following_rest, feature.distance_from_abs_dynamic,
                    #      feature.xml_position, feature.grace_order, feature.time_sig_num,
                    #      feature.time_sig_den, feature.no_following_note] #12
                    #     + feature.pitch + feature.tempo + feature.dynamic + feature.notation)
                    # train_x.append(
                    #     [feature.pitch_interval, feature.duration,
                    #      feature.duration_ratio, feature.beat_position, feature.measure_length,
                    #      feature.qpm_primo, feature.following_rest, feature.mean_piano_vel, feature.mean_forte_vel,
                    #      feature.mean_piano_mark, feature.mean_forte_mark, feature.distance_from_abs_dynamic,
                    #      feature.xml_position, feature.grace_order, feature.time_sig_num,
                    #      feature.time_sig_den, feature.no_following_note]  # 17
                    #     + feature.pitch + feature.tempo + feature.dynamic + feature.notation + feature.tempo_primo)
                    train_x.append(
                            [feature.pitch_interval, feature.duration,
                             feature.duration_ratio, feature.beat_importance, feature.measure_length,
                             feature.qpm_primo, feature.following_rest,  feature.distance_from_abs_dynamic,
                             feature.distance_from_recent_tempo,
                             feature.beat_position, feature.xml_position, feature.grace_order, feature.is_grace_note,
                             feature.followed_by_fermata_rest, feature.preceded_by_grace_note, feature.no_following_note]
                            + feature.pitch + feature.tempo + feature.dynamic + feature.time_sig_vec + feature.slur_beam_vec +  composer_vec + feature.notation + feature.tempo_primo)
                    # train_x.append(
                    #     [feature.pitch_interval, feature.duration,
                    #      feature.duration_ratio, feature.beat_position, feature.measure_length,
                    #     feature.following_rest, feature.distance_from_abs_dynamic,
                    #      feature.xml_position, feature.grace_order, feature.time_sig_num,
                    #      feature.time_sig_den, feature.no_following_note]  # 12
                    #     + feature.pitch + feature.tempo + feature.dynamic + feature.notation)

                    temp_y = [feature.qpm, feature.velocity, feature.xml_deviation,
                              feature.articulation, feature.pedal_refresh_time, feature.pedal_cut_time,
                              feature.pedal_at_start, feature.pedal_at_end, feature.soft_pedal,
                              feature.pedal_refresh, feature.pedal_cut] + feature.trill_param
                    # temp_y = [feature.passed_second, feature.duration_second, feature.velocity,
                    #           feature.pedal_refresh_time, feature.pedal_cut_time,
                    #           feature.pedal_at_start, feature.pedal_at_end, feature.soft_pedal,
                    #           feature.pedal_refresh, feature.pedal_cut]
                    train_y.append(temp_y)
                    align_matched_status.append(feature.align_matched)
                    # prev_feat[0] = feature.previous_tempo
                    prev_feat[0] = feature.qpm # for beat tempo network.
                    previous_y.append(prev_feat)
                    prev_feat = copy.copy(temp_y)
                    num_total_datapoint += 1
                    note_loc = feature.note_location
                    note_locations.append(note_loc)
                    # is_beat_list.append(feature.is_beat)
                    # beat_numbers.append(feature.beat_index)
                    # measure_numbers.append(feature.measure_index)
                    # voice_numbers.append(feature.voice)
            # windowed_train_x = make_windowed_data(train_x, input_length )
            # complete_xy.append([train_x, train_y, previous_y, beat_numbers, measure_numbers, voice_numbers])
            complete_xy.append([train_x, train_y, previous_y, note_locations, align_matched_status, score_graph, score])
            # key_changed_num = []
            # for i in range(3):
            #     key_change = 0
            #     while key_change == 0 or key_change in key_changed_num:
            #         key_change = random.randrange(-5, 7)
            #     train_x_aug = key_augmentation(train_x, key_change)
            #     complete_xy.append([train_x_aug, train_y, previous_y, beat_numbers, measure_numbers])
            #     key_changed_num.append(key_change)

    print('Total data point is ', num_total_datapoint)
    print('Number of total piece is ', num_piece, ' and total performance is ', num_perform)
    print(total_notes)
    num_input = len(train_x[0])
    num_output = len(train_y[0])

    print(train_x[0])
    print(train_y[0])


    if REGRESSION:
        complete_xy_normalized, means, stds = normalize_features(complete_xy, num_input, num_output, x_only=False)
        complete_xy_orig = complete_xy
        complete_xy = complete_xy_normalized
    else:
        complete_xy_normalized, means, stds = normalize_features(complete_xy, num_input, num_output, x_only=True)
        complete_xy_orig = complete_xy
        complete_xy = complete_xy_normalized
        complete_xy, bins = output_to_categorical(complete_xy)

    complete_xy_train = complete_xy[0:num_train]
    complete_xy_valid = complete_xy[num_train:]
    random.shuffle(complete_xy_train)
    random.shuffle(complete_xy_valid)



    for index1 in (0,1):
        for index2 in range(len(stds[index1])):
            std = stds[index1][index2]
            if std == 0:
                print('STD of ' + str(index1) + ',' + str(index2) + ' is zero')

    with open(save_name + ".dat", "wb") as f:
        pickle.dump({'train': complete_xy_train, 'valid': complete_xy_valid}, f, protocol=2)

    if REGRESSION:
        with open(save_name + "_stat.dat", "wb") as f:
            pickle.dump([means, stds], f, protocol=2)
    else:
        with open(save_name + "_stat.dat", "wb") as f:
            pickle.dump([means, stds, bins], f, protocol=2)

    num_output = len(complete_xy[0][1][0])
    print(num_input, num_output)


def get_mean_and_sd(performances, target_data, target_dimension):
    sum = 0
    squared_sum = 0
    count = 0
    for perf in performances:
        samples = perf[target_data]
        for sample in samples:
            value = sample[target_dimension]
            if target_data == 1 and 10< target_dimension <15 and value == 0:
                continue
            sum += value
            squared_sum += value * value
            count += 1
    if count != 0:
        data_mean = sum / count
        data_std = (squared_sum / count - data_mean ** 2) ** 0.5
    else:
        data_mean = 0
        data_std = 1
    return data_mean, data_std


def normalize_features(complete_xy, num_input, num_output, x_only=False):
    complete_xy_normalized = []
    means = [[], [], [], []]
    stds = [[], [], [], []]
    if x_only:
        index_list = [0]
    else:
        index_list = [0,1,2]

    for i1 in index_list:
        for i2 in range(NUM_NORMALIZE_FEATURE[i1]):
            mean_value, std_value = get_mean_and_sd(complete_xy, i1, i2)
            means[i1].append(mean_value)
            stds[i1].append(std_value)
    print(means)
    print(stds)

    if not x_only:
        means[2] = means[1]
        stds[2] = stds[1]

    for performance in complete_xy:
        complete_xy_normalized.append([])
        for index1 in index_list:
            complete_xy_normalized[-1].append([])
            for sample in performance[index1]:
                new_sample = []
                for index2 in range(NUM_NORMALIZE_FEATURE[index1]):
                    if not (stds[index1][index2] == 0 or isinstance(stds[index1][index2], complex)):
                        if index1 == 1 and 10 < index2 < 15 and sample[index2] == 0:
                            new_sample.append(0)
                        else:
                            new_sample.append((sample[index2] - means[index1][index2]) / stds[index1][index2])
                    else:
                        new_sample.append(0)
                if index1 == 0:
                    new_sample[NUM_NORMALIZE_FEATURE[index1]:num_input] = sample[
                                                                          NUM_NORMALIZE_FEATURE[index1]:num_input]
                else:
                    new_sample[NUM_NORMALIZE_FEATURE[index1]:num_output] = sample[
                                                                           NUM_NORMALIZE_FEATURE[index1]:num_output]
                complete_xy_normalized[-1][index1].append(new_sample)
        if x_only:
            complete_xy_normalized[-1].append(performance[1])
            complete_xy_normalized[-1].append(performance[2])

        complete_xy_normalized[-1].append(performance[3])
        complete_xy_normalized[-1].append(performance[4])
        complete_xy_normalized[-1].append(performance[5])

    return complete_xy_normalized, means, stds


def output_to_categorical(complete_xy):
    num_bins_by_feature = [100, 20, 20, 10, 10, 10]
    pedal_threshold = [-1, 30, 60, 128]
    xy_in_categorical = []
    entire_y = [xy[1] for xy in complete_xy]
    num_notes_of_perf = []
    entire_y_flattened = []

    bins = []

    for perf in entire_y:
        num_notes = len(perf)
        num_notes_of_perf.append(num_notes)
        if entire_y_flattened == []:
            entire_y_flattened = perf
        else:
            entire_y_flattened += perf

    y_as_mat = np.asarray(entire_y_flattened)
    trill_bool = y_as_mat[:,11] != 0

    for i in range(6):
        y_as_mat[:,i], temp_bin = pandas.qcut(y_as_mat[:,i], num_bins_by_feature[i], labels=False, retbins=True, duplicates='drop')
        bins.append(temp_bin)

    for i in range(6,11):
        y_as_mat[:, i] = pandas.cut(y_as_mat[:, i], pedal_threshold, labels=False)
        bins.append(pedal_threshold)

    for i in range(11,15):
        y_as_mat[trill_bool, i], temp_bin = pandas.qcut(y_as_mat[trill_bool, i], 5, labels=False, retbins=True, duplicates='drop')
        bins.append(temp_bin)

    num_perf = len(complete_xy)
    notes_range_index = 0
    for i in range(num_perf):
        num_notes = num_notes_of_perf[i]
        complete_xy[i][1] = y_as_mat[notes_range_index:notes_range_index+num_notes,:]
        notes_range_index += num_notes

    return complete_xy, bins


def key_augmentation(data_x, key_change):
    # key_change = 0
    data_x_aug = copy.deepcopy(data_x)
    pitch_start_index = 13
    # while key_change == 0:
    #     key_change = random.randrange(-5, 7)
    for data in data_x_aug:
        octave = data[pitch_start_index]
        pitch_class_vec = data[pitch_start_index+1:pitch_start_index+13]
        pitch_class = pitch_class_vec.index(1)
        new_pitch = pitch_class + key_change
        if new_pitch < 0:
            octave -= 0.25
        elif new_pitch > 12:
            octave += 0.25
        new_pitch = new_pitch % 12

        new_pitch_vec = [0] * 13
        new_pitch_vec[0] = octave
        new_pitch_vec[new_pitch+1] = 1

        data[pitch_start_index: pitch_start_index+13] = new_pitch_vec

    return data_x_aug



chopin_pairs, num_train_pairs = xml_matching.load_entire_subfolder('chopin_cleaned/Mozart/Piano_Sonatas/')
save_features_as_vector(chopin_pairs, num_train_pairs, 'slur_test')

