import copy
import json
import multiprocessing
import random
import subprocess
import time
from collections import Counter
import cv2
import os
from PIL import Image
import math
import glob
from torchvision import transforms
import torch
import onnxruntime
from scipy.special import softmax
import numpy as np

idx_to_class = {0: '中天楼_其他', 1: '中天楼_大门', 2: '华光楼_其他', 3: '华光楼_大门', 4: '川北道署_其他',
                5: '川北道署_大门', 6: '张飞庙_其他',
                7: '张飞庙_大门', 8: '文庙_其他', 9: '文庙_大门', 10: '牌坊', 11: '街景', 12: '贡院_其他',
                13: '贡院_大门'}
ffmpeg_path = "/home/nottingchain12/Documents/Listen/ffmpeg_bin/ffmpeg"  # ffmpeg路径


def extract_frames(video_path, reduced_size=256):
    # print(video_path)
    vc = cv2.VideoCapture()
    if not vc.open(video_path):
        # print("can not open the video!!!")
        vc.release()
        return None
    # # print(int(vc.get(cv2.CAP_PROP_FRAME_COUNT)), int(vc.get(cv2.CAP_PROP_FPS)), int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT)),
    #       int(vc.get(cv2.CAP_PROP_FRAME_WIDTH)))  # 2318 24 368 640
    index = 0
    interval = int(vc.get(cv2.CAP_PROP_FPS)) // 2
    img_numpy_list = []
    while True:
        _, frame = vc.read()
        if frame is None:
            break
        if index % interval == 0:
            # img_numpy_list.append(frame)
            img_numpy_list.append(cv2.resize(frame, (reduced_size, reduced_size))[16:240, 16:240])
        index += 1
    vc.release()
    # # print("Totally extract {:d} pics".format(len(img_numpy_list)))
    return img_numpy_list


def to_numpy(tensor):
    return tensor.detach().cpu().numpy() if tensor.requires_grad else tensor.cpu().numpy()


def normalize_meanstd(a, axis=None):
    # axis param denotes axes along which mean & std reductions are to be performed
    mean = np.mean(a, axis=axis, keepdims=True)
    std = np.sqrt(((a - mean) ** 2).mean(axis=axis, keepdims=True))
    return (a - mean) / std


def predict_(ort_session, img_numpy_list, transform, idx_to_class, batch_size=200):  #
    # proba_list = []
    # prediction_list = []
    # for i in range(math.ceil(len(img_numpy_list) / batch_size)):
    #     torch.cuda.empty_cache()
    #     # imgs = torch.cat(
    #     #     [torch.unsqueeze(transform(Image.fromarray(cv2.cvtColor(img_numpy, cv2.COLOR_BGR2RGB))), 0) for img_numpy in
    #     #      img_numpy_list[batch_size * i:batch_size * (i + 1)]], 0)
    #     # output = model(imgs.to(device))
    #     # output = model.forward(imgs.to(device))
    #     img = np.transpose(img_numpy_list[batch_size * i:batch_size * (i + 1)], (0,3, 2, 1))
    #     # img = np.expand_dims(img, 0)
    #     img = img.astype(np.float32)
    #     img /= 255
    #     # ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(imgs)}
    #     ort_inputs = {ort_session.get_inputs()[0].name: img.astype(np.float32)}
    #     ort_outs = ort_session.run(None, ort_inputs)
    #     output = softmax(ort_outs[0], axis=1)
    #     proba_list += np.max(output, axis=1).tolist()
    #     prediction_list += [idx_to_class[i] for i in np.argmax(output, axis=1).tolist()]
    #     # output = torch.nn.functional.softmax(output, dim=1)
    #     # proba, prediction = torch.max(output, 1)
    #     # proba_list += proba.detach().cpu().numpy().tolist()
    #     # prediction_list += [idx_to_class[i] for i in prediction.detach().cpu().numpy().tolist()]
    # return proba.detach().cpu().numpy().tolist(), [idx_to_class[i] for i in prediction.detach().cpu().numpy().tolist()]
    # # print(proba_list)
    # # print(prediction_list)

    # torch.cuda.empty_cache()
    # img = np.transpose(img_numpy_list, (0, 3, 2, 1))
    # # img = np.expand_dims(img, 0)
    # img = img.astype(np.float32)
    # img /= 255
    # # img=(img - np.array([0.485, 0.456, 0.406])) / np.array([0.485, 0.456, 0.406])
    # img=normalize_meanstd(img, axis=(1,2))
    # ort_inputs = {ort_session.get_inputs()[0].name: img}
    # ort_outs = ort_session.run(None, ort_inputs)
    # output = softmax(ort_outs[0], axis=1)
    # proba_list = np.max(output, axis=1).tolist()
    # prediction_list = [idx_to_class[i] for i in np.argmax(output, axis=1).tolist()]
    torch.cuda.empty_cache()
    imgs = torch.cat(
        [torch.unsqueeze(transform(Image.fromarray(cv2.cvtColor(img_numpy, cv2.COLOR_BGR2RGB))), 0) for img_numpy in
         img_numpy_list], 0)
    ort_inputs = {ort_session.get_inputs()[0].name: to_numpy(imgs)}
    ort_outs = ort_session.run(None, ort_inputs)
    output = torch.tensor(ort_outs[0], dtype=torch.float64)
    output = torch.nn.functional.softmax(output, dim=1)
    proba, prediction = torch.max(output, 1)
    proba_list = proba.detach().cpu().numpy().tolist()
    prediction_list = [idx_to_class[i] for i in prediction.detach().cpu().numpy().tolist()]
    # output = softmax(ort_outs[0], axis=1)
    # proba_list += np.max(output, axis=1).tolist()
    # prediction_list += [idx_to_class[i] for i in np.argmax(output, axis=1).tolist()]
    return proba_list, prediction_list


def analyze_prediction(proba_list, prediction_list, time_threshold=5, proportion_threshold=0.7,
                       probability_threshold=0.81, continuous_quantity=4):
    # # print(proba_list, prediction_list)
    recognized_fragments = []
    matching_start = None
    index_added = None
    len_ = len(proba_list) - 1
    for index, (proba, prediction) in enumerate(zip(proba_list, prediction_list)):
        if index_added and index_added > index:
            continue
        if proba >= probability_threshold:
            if matching_start != None:
                if prediction != prediction_list[matching_start]:
                    if index - matching_start >= continuous_quantity:
                        while True:
                            if matching_start - 1 < 0:
                                break
                            if prediction_list[matching_start - 1] == prediction_list[matching_start]:
                                matching_start -= 1
                            else:
                                break
                        recognized_fragments.append(
                            (matching_start / 2, (index - 1) / 2, prediction_list[matching_start]))
                    matching_start = index
                else:
                    if index == len_:
                        if index - matching_start >= continuous_quantity:
                            while True:
                                if matching_start - 1 < 0:
                                    break
                                if prediction_list[matching_start - 1] == prediction_list[matching_start]:
                                    matching_start -= 1
                                else:
                                    break
                            recognized_fragments.append(
                                (matching_start / 2, index / 2, prediction_list[matching_start]))
            else:
                matching_start = index
        else:
            if matching_start != None:
                if index - matching_start >= continuous_quantity:
                    while True:
                        if matching_start - 1 < 0:
                            break
                        if prediction_list[matching_start - 1] == prediction_list[matching_start]:
                            matching_start -= 1
                        else:
                            break
                    while True:
                        try:
                            if prediction_list[index] == prediction_list[matching_start]:
                                index += 1
                                index_added = index
                            else:
                                break
                        except:
                            break
                    recognized_fragments.append((matching_start / 2, (index - 1) / 2, prediction_list[matching_start]))
                matching_start = None
    if not recognized_fragments:
        # print(recognized_fragments)
        class_name, count_num = Counter(prediction_list).most_common(1)[0]
        proportion = count_num / len(prediction_list)
        if proportion >= proportion_threshold:
            if len(prediction_list) <= time_threshold * 2 + 1:
                recognized_fragments.append((0, len_ / 2, class_name))
            else:
                for index, prediction in enumerate(prediction_list):
                    if prediction == class_name:
                        if matching_start == None:
                            matching_start = index
                        else:
                            if index == len_:
                                if index - matching_start >= continuous_quantity:
                                    recognized_fragments.append(
                                        (matching_start / 2, index / 2, class_name))
                                    # print(recognized_fragments)
                    else:
                        if matching_start != None:
                            if index - matching_start >= continuous_quantity:
                                recognized_fragments.append((matching_start / 2, (index - 1) / 2, class_name))
                                matching_start = None
                                # print(recognized_fragments)
    if not recognized_fragments:
        class_name, count_num = Counter([i.split('_')[0] for i in prediction_list]).most_common(1)[0]
        class_name, count_num = Counter([i for i in prediction_list if class_name in i]).most_common(1)[0]

        recognized_fragments.append((0, len_ / 2, class_name))
    # print(recognized_fragments)
    return recognized_fragments


def gen_time_str(time_number):
    m, s = divmod(time_number, 60)
    h, m = divmod(m, 60)
    time_str = "%02d:%02d:%02d" % (h, m, s)
    if time_number % 1:
        time_str += f".%03d" % (time_number % 1 * 1000)
    return time_str


def second_cycle_processing(video_fragments_list):
    splicing_fragments_dict2, video_fragments_sort_list = {}, []
    for video_fragments__ in video_fragments_list:
        dict_temp = {}
        for video_fragment_ in video_fragments__[1]:
            class_name = video_fragment_[2].split('_')[0]
            if class_name in dict_temp:
                dict_temp[class_name] += video_fragment_[1] - video_fragment_[0]  # 时长
            else:
                dict_temp[class_name] = video_fragment_[1] - video_fragment_[0]
        sorted_list = sorted(dict_temp.items(), key=lambda x: x[1], reverse=True)
        if sorted_list[0][0] in splicing_fragments_dict2:
            splicing_fragments_dict2[sorted_list[0][0]] += [
                (video_fragments__[0], [a for a in video_fragments__[1] if a[2].split('_')[0] == sorted_list[0][0]])]
        else:
            splicing_fragments_dict2[sorted_list[0][0]] = [
                (video_fragments__[0], [a for a in video_fragments__[1] if a[2].split('_')[0] == sorted_list[0][0]])]
        video_fragments_sort_list.append((video_fragments__[0], sorted_list))
    return splicing_fragments_dict2, video_fragments_sort_list


def third_cycle_processing(video_fragments_sort_list, video_fragments_list):
    splicing_fragments_dict3 = {}
    for indexx, video_fragments_sort in enumerate(video_fragments_sort_list):
        if video_fragments_sort[1][1][0] in splicing_fragments_dict3:
            splicing_fragments_dict3[video_fragments_sort[1][1][0]] += [(video_fragments_sort[0],
                                                                         [video_fragments for video_fragments in
                                                                          video_fragments_list[indexx][1] if
                                                                          video_fragments[2].split('_')[0] ==
                                                                          video_fragments_sort[1][1][0]])]
        else:
            splicing_fragments_dict3[video_fragments_sort[1][1][0]] = [(video_fragments_sort[0],
                                                                        [video_fragments for video_fragments in
                                                                         video_fragments_list[indexx][1] if
                                                                         video_fragments[2].split('_')[0] ==
                                                                         video_fragments_sort[1][1][0]])]
    return splicing_fragments_dict3


def multiple_fragments_distribution(sorted_multiple_num, need_replace_num):  ##
    sorted_list_len = len(sorted_multiple_num)
    multiple_fragments_dict = {}
    j = 0
    i = 0
    while j < need_replace_num:
        while sorted_multiple_num[i][1] < 1:
            if i + 1 >= sorted_list_len:
                i = 0
            else:
                i += 1
        sorted_multiple_num[i][1] -= 1
        if sorted_multiple_num[i][0] in multiple_fragments_dict:
            multiple_fragments_dict[sorted_multiple_num[i][0]] += 1
        else:
            multiple_fragments_dict[sorted_multiple_num[i][0]] = 1
        if i + 1 >= sorted_list_len:
            i = 0
        else:
            i += 1
        j += 1
    # print("multiple_fragments_dict:", multiple_fragments_dict)
    return multiple_fragments_dict


def update_temp_list(temp_list, hierarchy_dict, class_name, splicing_fragments_dict2, splicing_fragments_dict3):  ##
    if hierarchy_dict[class_name] == 1:
        if class_name in splicing_fragments_dict2:
            temp_list += [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict2[class_name] for j
                          in i[1]]
        if class_name in splicing_fragments_dict3:
            temp_list += [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict3[class_name] for j
                          in i[1]]
    elif hierarchy_dict[class_name] == 2:
        if class_name in splicing_fragments_dict3:
            temp_list += [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict3[class_name] for j
                          in i[1]]
    return temp_list


def change_temp_position(temp_list):
    gate_list = []
    for index, temp_ in enumerate(temp_list):
        temp_split = temp_[3].split("_")
        if len(temp_split) == 2:
            if temp_split[1] == '大门':
                gate_list.append(index)
    # gate_list = [index for index, temp_ in enumerate(temp_list) if temp_[3].split("_")[1] == '大门']
    for index in gate_list:
        list_pop = temp_list.pop(index)
        temp_list.insert(0, list_pop)
    # return temp_list


def update_clazz_distribution(temp_list, num_all, fragment_second):  ##
    # print("update_clazz_distribution")
    change_temp_position(temp_list)
    temp_time_list = []
    for i in range(num_all):
        if temp_list[i][2] - temp_list[i][1] == fragment_second:
            temp_time_list.append(temp_list[i])
        else:
            start_time = (temp_list[i][1] + temp_list[i][2] - fragment_second) / 2
            temp_time_list.append((temp_list[i][0], start_time, start_time + fragment_second, temp_list[i][3]))
    return temp_time_list


def update_clazz_split_distribution(temp_list_dict, temp_list, fragment_interval_second, fragment_second):  ##
    finally_temp_list = []
    together_second = fragment_second + fragment_interval_second
    for k, j in temp_list_dict.items():
        len_section = (temp_list[k][2] - temp_list[k][1]) / j
        if len_section < fragment_second + (j - 1) / j * fragment_interval_second:
            raise Exception("len_section小了小了!")
        elif len_section < together_second:
            for v in range(j):
                start_point = temp_list[k][1] + v * together_second
                finally_temp_list.append((temp_list[k][0], start_point, start_point + fragment_second, temp_list[k][3]))
        else:
            half_len = fragment_second / 2
            for v in range(j):
                start_point = (temp_list[k][1] + v * len_section + temp_list[k][
                    1] + v * len_section + len_section) / 2 - half_len
                finally_temp_list.append((temp_list[k][0], start_point, start_point + fragment_second, temp_list[k][3]))
            if start_point + fragment_second > temp_list[k][2]:
                raise Exception("超出边界了！")
    return finally_temp_list


def update_clazz_single_distribution(splicing_fragments_dict_new, class_name, class_name_dict, fragment_num, temp_list,
                                     fragment_interval_second, fragment_second):  ##
    # print("update_clazz_single_distribution:")
    if class_name_dict[class_name][1] >= fragment_num:  # 其实这边可以优化分布
        splicing_fragments_dict_new[class_name] = update_clazz_distribution(temp_list, fragment_num, fragment_second)
    else:
        change_temp_position(temp_list)
        max_split_num_dict = {
            index: int((item[2] - item[1] - fragment_second) // (
                    fragment_interval_second + fragment_second)) + 1 for
            index, item in enumerate(temp_list)}
        temp_list_dict = multiple_fragments_distribution([list(item) for item in list(max_split_num_dict.items())],
                                                         fragment_num)
        splicing_fragments_dict_new[class_name] = update_clazz_split_distribution(temp_list_dict, temp_list,
                                                                                  fragment_interval_second,
                                                                                  fragment_second)
    # print(f"splicing_fragments_dict_new[{class_name}]::", splicing_fragments_dict_new[class_name])


def update_clazz_multi_distribution(multiple_num_dict, class_name, class_frame_num_dict, multiple_time_dict,
                                    multiple_num, class_name_dict, temp_list,
                                    hierarchy_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                                    splicing_fragments_dict_new, fragment_second,
                                    fragment_interval_second):
    # print("update_clazz_multi_distribution:")
    multiple_num_data = multiple_num_dict[class_name] + class_frame_num_dict[
        class_name] if class_name in multiple_num_dict else class_frame_num_dict[class_name]
    multiple_time_data = multiple_time_dict[class_name] + class_frame_num_dict[
        class_name] if class_name in multiple_time_dict else class_frame_num_dict[class_name]
    if multiple_num <= multiple_num_data:
        # print("片段个数足够分配！")
        if class_name_dict[class_name][1] < multiple_num:
            temp_list = update_temp_list(temp_list, hierarchy_dict, class_name,
                                         splicing_fragments_dict2,
                                         splicing_fragments_dict3)
        if len(temp_list) < multiple_num:
            raise Exception("temp_list长度不够！")
        splicing_fragments_dict_new[class_name] = update_clazz_distribution(temp_list, multiple_num,
                                                                            fragment_second)
    elif multiple_num <= multiple_time_data:
        # print("片段个数分不开！")
        temp_list = update_temp_list(temp_list, hierarchy_dict, class_name,
                                     splicing_fragments_dict2,
                                     splicing_fragments_dict3)
        change_temp_position(temp_list)
        max_split_num_dict = {
            index: int(
                (item[2] - item[1] - fragment_second) // (fragment_interval_second + fragment_second)) + 1 for
            index, item in enumerate(temp_list)}
        temp_list_dict = multiple_fragments_distribution(
            [list(item) for item in list(max_split_num_dict.items())], multiple_num)
        splicing_fragments_dict_new[class_name] = update_clazz_split_distribution(temp_list_dict, temp_list,
                                                                                  fragment_interval_second,
                                                                                  fragment_second)
    else:
        raise Exception("连片段总时长都满足不了！")
    # print(f"splicing_fragments_dict_new[{class_name}]:", splicing_fragments_dict_new[class_name])


def allocation_by_time(replace_time_dict, multiple_time_dict, class_frame_num_dict, splicing_fragments_dict,
                       splicing_fragments_dict_new,
                       already_processed, remainder_class_name_set,
                       multiple_num_dict, class_name_dict, hierarchy_dict, splicing_fragments_dict2,
                       splicing_fragments_dict3, fragment_interval_second, fragment_second):  ##
    # print("allocation_by_time:")
    for class_name in splicing_fragments_dict.keys():  # 时间上满足了
        if already_processed:
            if class_name in already_processed:
                continue
        if class_name in remainder_class_name_set:  # 干净了
            del splicing_fragments_dict[class_name]
            continue
        # if class_name in extra_class_name_set:
        #     continue
        temp_list = [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict[class_name] for j in i[1]]
        if class_name in replace_time_dict:
            multiple_num = sum([i[1] for i in replace_time_dict[class_name]]) + class_frame_num_dict[class_name]

            update_clazz_multi_distribution(multiple_num_dict, class_name, class_frame_num_dict, multiple_time_dict,
                                            multiple_num, class_name_dict, temp_list,
                                            hierarchy_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                                            splicing_fragments_dict_new, fragment_second,
                                            fragment_interval_second)
        else:
            update_clazz_single_distribution(splicing_fragments_dict_new, class_name, class_name_dict,
                                             class_frame_num_dict[class_name], temp_list, fragment_interval_second,
                                             fragment_second)


def internal_single_assignment(splicing_fragments_dict, splicing_fragments_dict_new, already_processed, class_name_dict,
                               class_frame_num_dict,
                               fragment_interval_second, fragment_second, remainder_class_name_set=None):  ##
    for class_name in splicing_fragments_dict.keys():
        # print("class_name:", class_name)
        if already_processed:
            if class_name in already_processed:
                continue
        if remainder_class_name_set:
            if class_name in remainder_class_name_set:  # 干净了
                del splicing_fragments_dict[class_name]
                continue
        temp_list = [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict[class_name] for j in i[1]]
        update_clazz_single_distribution(splicing_fragments_dict_new, class_name, class_name_dict,
                                         class_frame_num_dict[class_name], temp_list, fragment_interval_second,
                                         fragment_second)


def is_meet_need(multiple_dict, need_replace, class_frame_num_dict):
    # print("multiple_dict:", multiple_dict)
    need_replace_dict = {k: v for k, v in class_frame_num_dict.items() if k in need_replace}
    sorted_need_num = [list(item) for item in sorted(need_replace_dict.items(), key=lambda x: x[1], reverse=False)]
    replace_dict = {}
    for i in range(len(sorted_need_num) - 1, -1, -1):
        for k, v in multiple_dict.items():  # 可以优化
            if sorted_need_num[i][1] <= v:
                if sorted_need_num[i][1] == v:
                    del multiple_dict[k]
                else:
                    multiple_dict[k] -= sorted_need_num[i][1]
                if k in replace_dict:
                    replace_dict[k].append((sorted_need_num[i]))
                else:
                    replace_dict[k] = [sorted_need_num[i]]
                sorted_need_num.pop(i)
                break
    # print(f"还剩{len(sorted_need_num)}个类别景点没有被满足！")
    # print("replace_dict:", replace_dict)
    return sorted_need_num, replace_dict


def redistribution(previous_class_name, multiple_time_dict, replace_time_dict, class_frame_num_dict,
                   splicing_fragments_dict, multiple_num_dict,
                   class_name_dict, hierarchy_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                   splicing_fragments_dict_new,
                   fragment_second, fragment_interval_second, distribution_master_list, class_name_index):
    remedied = None
    if previous_class_name in multiple_time_dict:
        # distribution_num_sum=sum([num for i,num in zip(distribution_master_list,class_frame_num_dict.values()) if i==previous_class_name])
        try:
            distribution_num_sum = sum([i[1] for i in replace_time_dict[previous_class_name]]) + class_frame_num_dict[
                previous_class_name] + 1
        except:
            distribution_num_sum = class_frame_num_dict[previous_class_name] + 1
        if distribution_num_sum <= multiple_time_dict[previous_class_name]:
            temp_list = [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict[previous_class_name] for j in
                         i[1]]
            update_clazz_multi_distribution(multiple_num_dict, previous_class_name, class_frame_num_dict,
                                            multiple_time_dict, distribution_num_sum, class_name_dict,
                                            temp_list,
                                            hierarchy_dict, splicing_fragments_dict2,
                                            splicing_fragments_dict3, splicing_fragments_dict_new,
                                            fragment_second,
                                            fragment_interval_second)
            distribution_master_list[class_name_index] = previous_class_name
            remedied = previous_class_name
    return remedied


def search_redistribution(multiple_time_dict, replace_time_dict, class_frame_num_dict,
                          splicing_fragments_dict, multiple_num_dict,
                          class_name_dict, hierarchy_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                          splicing_fragments_dict_new,
                          fragment_second, fragment_interval_second, distribution_master_list,
                          class_name_index, class_name_index_):
    if type(distribution_master_list[class_name_index_]) == str:
        previous_class_name = distribution_master_list[class_name_index_]

        remedied = redistribution(previous_class_name, multiple_time_dict, replace_time_dict, class_frame_num_dict,
                                  splicing_fragments_dict, multiple_num_dict,
                                  class_name_dict, hierarchy_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                                  splicing_fragments_dict_new,
                                  fragment_second, fragment_interval_second, distribution_master_list,
                                  class_name_index)
    else:
        previous_class_name = distribution_master_list[class_name_index_][0][3].split("_")[1]

        remedied = redistribution(previous_class_name, multiple_time_dict, replace_time_dict,
                                  class_frame_num_dict,
                                  splicing_fragments_dict, multiple_num_dict,
                                  class_name_dict, hierarchy_dict, splicing_fragments_dict2,
                                  splicing_fragments_dict3,
                                  splicing_fragments_dict_new,
                                  fragment_second, fragment_interval_second, distribution_master_list,
                                  class_name_index)
    return remedied


def process_extra_class(extra_class_name_set, class_name_list, distribution_master_list, multiple_time_dict,
                        replace_time_dict, class_frame_num_dict,
                        splicing_fragments_dict, multiple_num_dict,
                        class_name_dict, hierarchy_dict, splicing_fragments_dict2,
                        splicing_fragments_dict3,
                        splicing_fragments_dict_new,
                        fragment_second, fragment_interval_second, class_max_index, class_video_dict):  # 废
    for class_name in extra_class_name_set:
        if class_name in splicing_fragments_dict:
            ite = splicing_fragments_dict[class_name][0]
            if ite[1][0][1] - ite[1][0][0] == fragment_second:
                splicing_fragments_dict_new[class_name] = [(ite[0], ite[1][0][0], ite[1][0][1], class_name)]
            else:
                start_time = (ite[1][0][0] + ite[1][0][1] - fragment_second) / 2
                splicing_fragments_dict_new[class_name] = [
                    (ite[0], start_time, start_time + fragment_second, class_name)]
        else:
            class_name_index = class_name_list.index(class_name)
            remedied = False
            if class_name_index != 0:
                pass
            if not remedied:
                if class_name_index != class_max_index:
                    pass
            if not remedied:
                splicing_fragments_dict_new[class_name] = [
                    (random.choice(class_video_dict[class_name]), 0, fragment_second, class_name)]


def adjust_position(class_frame_num_dict, class_name_list, extra_class_name_set,
                    splicing_fragments_dict, splicing_fragments_dict_new, replace_time_dict,
                    multiple_num_dict, multiple_time_dict, class_name_dict, hierarchy_dict, splicing_fragments_dict2,
                    splicing_fragments_dict3, fragment_second, fragment_interval_second, class_video_dict):
    # print("adjust_position:")
    distribution_master_list = [[None for j in range(i)] for i in class_frame_num_dict.values()]
    distribution_interval_point = {}
    shift_index = {}
    class_max_index = len(class_name_list) - 1
    for index, class_name in enumerate(class_name_list):
        # print(index, class_name)
        if class_name in splicing_fragments_dict_new:
            if class_name in replace_time_dict:
                if class_frame_num_dict[class_name] <= len(splicing_fragments_dict_new[class_name]):
                    distribution_master_list[index] = class_name
                else:
                    raise Exception("长度不对！")
            else:
                if distribution_master_list[index][0]:
                    raise Exception("已经有值！")
                else:
                    if len(splicing_fragments_dict_new[class_name]) == class_frame_num_dict[class_name]:
                        distribution_master_list[index] = splicing_fragments_dict_new[class_name]
                    else:
                        # print(splicing_fragments_dict_new[class_name])
                        # print(class_frame_num_dict[class_name])
                        raise Exception("frame个数不一致！")
    # print("distribution_master_list1:", distribution_master_list)
    for class_name, replace_item in replace_time_dict.items():
        for class_name2, num in replace_item:  # 这边要注意牌坊和街景也会被换位置，目前为1没问题
            if class_name in distribution_interval_point:
                start_point, end_point = distribution_interval_point[class_name]
                if class_name2 in shift_index:
                    index2 = shift_index[class_name2]
                else:
                    index2 = class_name_list.index(class_name2)
                if start_point - 1 == index2:
                    distribution_master_list[index2] = class_name
                    distribution_interval_point[class_name] = [start_point - 1, end_point]
                elif end_point + 1 == index2:
                    distribution_master_list[index2] = class_name
                    distribution_interval_point[class_name] = [start_point, end_point + 1]
                else:
                    handled = False
                    if end_point < class_max_index:
                        if type(distribution_master_list[end_point + 1]) == list:
                            if len(distribution_master_list[end_point + 1]) == class_frame_num_dict[class_name2]:
                                if distribution_master_list[end_point + 1][0] == None:
                                    shift_index_values = list(shift_index.values())
                                    if end_point + 1 in shift_index_values:
                                        class_name3 = list(shift_index.keys())[shift_index_values.index(end_point + 1)]
                                    else:
                                        class_name3 = class_name_list[end_point + 1]

                                    shift_index[class_name3] = index2
                                distribution_master_list[index2] = distribution_master_list[end_point + 1]
                                distribution_master_list[end_point + 1] = class_name
                                handled = True
                                distribution_interval_point[class_name] = [start_point, end_point + 1]
                    if not handled:
                        if start_point > 0:
                            if type(distribution_master_list[start_point - 1]) == list:
                                if len(distribution_master_list[start_point - 1]) == class_frame_num_dict[class_name2]:
                                    if distribution_master_list[start_point - 1][0] == None:
                                        shift_index_values = list(shift_index.values())
                                        if start_point - 1 in shift_index_values:
                                            class_name3 = list(shift_index.keys())[
                                                shift_index_values.index(start_point - 1)]
                                        else:
                                            class_name3 = class_name_list[start_point - 1]

                                        shift_index[class_name3] = index2
                                    distribution_master_list[index2] = distribution_master_list[start_point - 1]
                                    distribution_master_list[start_point - 1] = class_name
                                    handled = True
                                    distribution_interval_point[class_name] = [start_point - 1, end_point]
                    if not handled:
                        # 暂时没有办法了 不能贴在一起了
                        distribution_master_list[index2] = class_name
            else:
                index1 = class_name_list.index(class_name)
                if class_name2 in shift_index:
                    index2 = shift_index[class_name2]
                else:
                    index2 = class_name_list.index(class_name2)
                index_diff = index1 - index2
                if index_diff == 1:
                    distribution_master_list[index2] = class_name
                    distribution_interval_point[class_name] = [index1 - 1, index1]
                elif index_diff == -1:
                    distribution_master_list[index2] = class_name
                    distribution_interval_point[class_name] = [index1, index1 + 1]
                else:
                    handled = False
                    if index1 < class_max_index:
                        if type(distribution_master_list[index1 + 1]) == list:
                            if len(distribution_master_list[index1 + 1]) == class_frame_num_dict[class_name2]:
                                if distribution_master_list[index1 + 1][0] == None:
                                    shift_index_values = list(shift_index.values())
                                    if index1 + 1 in shift_index_values:
                                        class_name3 = list(shift_index.keys())[shift_index_values.index(index1 + 1)]
                                    else:
                                        class_name3 = class_name_list[index1 + 1]

                                    shift_index[class_name3] = index2
                                distribution_master_list[index2] = distribution_master_list[index1 + 1]
                                distribution_master_list[index1 + 1] = class_name
                                handled = True
                                distribution_interval_point[class_name] = [index1, index1 + 1]
                    if not handled:
                        if index1 > 0:
                            if type(distribution_master_list[index1 - 1]) == list:
                                if len(distribution_master_list[index1 - 1]) == class_frame_num_dict[class_name2]:
                                    if distribution_master_list[index1 - 1][0] == None:
                                        shift_index_values = list(shift_index.values())
                                        if index1 - 1 in shift_index_values:
                                            class_name3 = list(shift_index.keys())[
                                                shift_index_values.index(index1 - 1)]
                                        else:
                                            class_name3 = class_name_list[index1 - 1]

                                        shift_index[class_name3] = index2
                                    distribution_master_list[index2] = distribution_master_list[index1 - 1]
                                    distribution_master_list[index1 - 1] = class_name
                                    handled = True
                                    distribution_interval_point[class_name] = [index1 - 1, index1]
                    if not handled:
                        # 暂时没有办法了 不能贴在一起了
                        distribution_master_list[index2] = class_name
            if class_name2 in shift_index:
                del shift_index[class_name2]
    # print("distribution_master_list2:", distribution_master_list)
    remedied_dict = {}
    for class_name in extra_class_name_set:
        # print(class_name)
        class_name_index = class_name_list.index(class_name)
        item = distribution_master_list[class_name_index]
        if item[0] == None:
            remedied = None
            if class_name_index != 0:
                remedied = search_redistribution(multiple_time_dict, replace_time_dict, class_frame_num_dict,
                                                 splicing_fragments_dict, multiple_num_dict,
                                                 class_name_dict, hierarchy_dict, splicing_fragments_dict2,
                                                 splicing_fragments_dict3,
                                                 splicing_fragments_dict_new,
                                                 fragment_second, fragment_interval_second, distribution_master_list,
                                                 class_name_index, class_name_index - 1)
            # print(remedied)
            if remedied == None:
                if class_name_index != class_max_index:
                    remedied = search_redistribution(multiple_time_dict, replace_time_dict, class_frame_num_dict,
                                                     splicing_fragments_dict, multiple_num_dict,
                                                     class_name_dict, hierarchy_dict, splicing_fragments_dict2,
                                                     splicing_fragments_dict3,
                                                     splicing_fragments_dict_new,
                                                     fragment_second, fragment_interval_second,
                                                     distribution_master_list,
                                                     class_name_index, class_name_index + 1)
            # print(remedied)
            if remedied == None:
                distribution_master_list[class_name_index] = [
                    (random.choice(class_video_dict[class_name]), 0, fragment_second, class_name)]
            else:
                if remedied in remedied_dict:
                    remedied_dict[remedied] += 1
                else:
                    remedied_dict[remedied] = 1
        elif type(item[0]) == tuple:
            # print(f"{class_name} 已经填充了！")
            pass
        else:
            raise Exception(f"{class_name} 出现未知类型-->{item[0]}！")
    for class_name in remedied_dict:
        update_clazz_multi_distribution(multiple_num_dict, class_name, class_frame_num_dict, multiple_time_dict,
                                        len(splicing_fragments_dict_new[class_name]) + remedied_dict[class_name],
                                        class_name_dict,
                                        [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict[class_name] for j in
                                         i[1]],
                                        hierarchy_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                                        splicing_fragments_dict_new, fragment_second,
                                        fragment_interval_second)
    # print("remedied_dict:", remedied_dict)
    # print("distribution_master_list3:", distribution_master_list)
    duplicate_allocation = {}
    # for index in range(class_max_index + 1):
    for index, class_name in enumerate(class_name_list):
        item = distribution_master_list[index]
        if type(item) == str:
            length = class_frame_num_dict[class_name_list[index]]
            if item in duplicate_allocation:
                start_ = duplicate_allocation[item]
                distribution_master_list[index] = splicing_fragments_dict_new[item][start_:start_ + length]
                duplicate_allocation[item] += length
            else:
                distribution_master_list[index] = splicing_fragments_dict_new[item][:length]
                duplicate_allocation[item] = length
        else:
            if item[0] == None:
                # if class_name in extra_class_name_set:
                #     pass
                # else:
                #     raise Exception("还有为None没有处理的情况！")
                raise Exception("还有为None没有处理的情况！")
    # print("distribution_master_list4:", distribution_master_list)
    return distribution_master_list


def distribution_procedure(video_path_list, recognized_fragments_list, class_video_dict, class_frame_num_dict,
                           extra_class_name_set,
                           fragment_second=2, fragment_interval_second=1,
                           # all_class_name_set={'贡院', '川北道署', '中天楼', '张飞庙', '文庙', '华光楼' },
                           all_class_name_set={'贡院', '川北道署', '中天楼', '张飞庙', '文庙', '华光楼', '牌坊',
                                               '街景'},
                           ):
    material_included_list = []
    # extra_class_name_set={'牌坊','街景'}
    class_name_list = list(class_frame_num_dict.keys())
    min_fragment_num = min(list(class_frame_num_dict.values()))
    video_fragments_list = []
    for video_path, recognized_fragments in zip(video_path_list, recognized_fragments_list):
        recognized_fragments = [j for j in recognized_fragments if j[1] - j[0] >= fragment_second]
        if recognized_fragments:
            video_fragments_list.append((video_path, recognized_fragments))
    splicing_fragments_dict = {}  # 这个类别全的
    splicing_fragments_dict_new = {}
    # print("video_fragments_list:", video_fragments_list)
    for i in range(len(video_fragments_list) - 1, -1, -1):
        if video_fragments_list[i][1]:
            class_name_set = set([ii[2].split('_')[0] for ii in video_fragments_list[i][1]])
            if len(class_name_set) == 1:
                class_name = class_name_set.pop()
                if class_name in splicing_fragments_dict:
                    splicing_fragments_dict[class_name].append(video_fragments_list[i])
                else:
                    splicing_fragments_dict[class_name] = [video_fragments_list[i]]
                video_fragments_list.pop(i)
        else:
            video_fragments_list.pop(i)
    # print("splicing_fragments_dict:", splicing_fragments_dict)
    splicing_fragments_dict2 = {}  # 有漏的
    splicing_fragments_dict3 = {}  # 有漏的
    hierarchy_dict = {}
    # for class_name_ in class_name_list:  # 最好再加上漏的
    for class_name_ in all_class_name_set:
        # search_down = False
        search_down = True
        if class_name_ in splicing_fragments_dict:
            if class_name_ in class_frame_num_dict:
                fragments_sum = sum([len(i[1]) for i in splicing_fragments_dict[class_name_]])
                # if fragments_sum < class_frame_num_dict[class_name_]:
                if fragments_sum >= class_frame_num_dict[class_name_]:
                    # search_down = True
                    search_down = False
        # else:
        #     search_down = True
        if search_down:
            if not splicing_fragments_dict2:
                splicing_fragments_dict2, video_fragments_sort_list = second_cycle_processing(
                    video_fragments_list)
            # search_down2 = False
            search_down2 = True
            if class_name_ in splicing_fragments_dict2:
                if class_name_ in splicing_fragments_dict:
                    splicing_fragments_dict[class_name_] += splicing_fragments_dict2[class_name_]
                else:
                    splicing_fragments_dict[class_name_] = splicing_fragments_dict2[class_name_]
                if class_name_ in class_frame_num_dict:
                    fragments_sum = sum([len(i[1]) for i in splicing_fragments_dict[class_name_]])
                    # if fragments_sum < class_frame_num_dict[class_name_]:
                    if fragments_sum >= class_frame_num_dict[class_name_]:
                        # search_down2 = True
                        search_down2 = False
            # else:
            #     search_down2 = True
            if search_down2:
                hierarchy_dict[class_name_] = 3
                if not splicing_fragments_dict3:
                    splicing_fragments_dict3 = third_cycle_processing(video_fragments_sort_list,
                                                                      video_fragments_list)
                if class_name_ in splicing_fragments_dict3:
                    if class_name_ in splicing_fragments_dict:
                        splicing_fragments_dict[class_name_] += splicing_fragments_dict3[class_name_]
                    else:
                        splicing_fragments_dict[class_name_] = splicing_fragments_dict3[class_name_]
                    # 其实这边也不能保证数量已经够了，但不会再找下去了
                else:
                    # print(f"{class_name_} 这里基本上是没有满足的！")
                    pass
            else:
                hierarchy_dict[class_name_] = 2
        else:
            hierarchy_dict[class_name_] = 1
    # print("splicing_fragments_dict:", splicing_fragments_dict)
    # print("splicing_fragments_dict2:", splicing_fragments_dict2)
    # print("splicing_fragments_dict3:", splicing_fragments_dict3)
    class_name_dict = {
        class_name: [len(splicing_fragments_value), sum([len(i[1]) for i in splicing_fragments_value]),
                     sum([int((j[1] - j[0] - fragment_second) // (fragment_interval_second + fragment_second)) + 1 for i
                          in splicing_fragments_value for j in i[1]])] for
        class_name, splicing_fragments_value in splicing_fragments_dict.items()}
    class_name_dict2 = {
        class_name: [len(splicing_fragments_value), sum([len(i[1]) for i in splicing_fragments_value]),
                     sum([int(
                         (j[1] - j[0] - fragment_second) // (fragment_interval_second + fragment_second)) + 1
                          for i
                          in splicing_fragments_value for j in i[1]])] for
        class_name, splicing_fragments_value in splicing_fragments_dict2.items()}
    class_name_dict3 = {
        class_name: [len(splicing_fragments_value), sum([len(i[1]) for i in splicing_fragments_value]),
                     sum([int(
                         (j[1] - j[0] - fragment_second) // (fragment_interval_second + fragment_second)) + 1
                          for i
                          in splicing_fragments_value for j in i[1]])] for
        class_name, splicing_fragments_value in splicing_fragments_dict3.items()}
    # print("class_name_dict:", class_name_dict)  # 全的
    # print("class_name_dict2:", class_name_dict2)  # 全的
    # print("class_name_dict3:", class_name_dict3)  # 全的
    need_replace = set()
    already_processed = set()
    for class_name in class_name_list:
        if class_name in class_name_dict:
            if class_name_dict[class_name][1] < class_frame_num_dict[class_name]:
                if class_name_dict[class_name][2] < class_frame_num_dict[class_name]:
                    # if class_name_dict[class_name][2] >= class_frame_num_dict[class_name] / 2:
                    listt = []
                    gate_list = [(index1, index2) for index1, splicing_fragments_item in
                                 enumerate(splicing_fragments_dict[class_name]) for index2, splicing_fragment_item in
                                 enumerate(splicing_fragments_item[1]) if
                                 splicing_fragment_item[2].split("_")[1] == '大门']
                    # if not gate_list:
                    #     gate_list=[(-1,-1)]
                    gate_list_new = []
                    for inde, splicing_fragments_item in enumerate(splicing_fragments_dict[class_name]):
                        for inde2, splicing_fragment_item in enumerate(splicing_fragments_item[1]):
                            is_gate = False
                            for gate in gate_list:
                                if inde == gate[0] and inde2 == gate[1]:
                                    is_gate = True
                                    break
                            # if is_gate:
                            #     continue
                            split_section_time = int((splicing_fragment_item[1] - splicing_fragment_item[
                                0] - fragment_second) // (fragment_interval_second + fragment_second)) + 1
                            for i in range(split_section_time):
                                start_time = splicing_fragment_item[0] + i * (
                                        fragment_second + fragment_interval_second)
                                # classs_name=class_name+'_'
                                # classs_name+="大门" if is_gate else "其他"
                                # itemm=(splicing_fragments_item[0],start_time,start_time + fragment_second,classs_name)
                                # if is_gate:
                                #     gate_list_new.append(itemm)
                                # else:
                                #     listt.append(itemm)
                                # classs_name = class_name + '_'
                                # classs_name += "大门" if is_gate else "其他"
                                # itemm = (
                                # splicing_fragments_item[0], start_time, start_time + fragment_second, classs_name)
                                if is_gate:
                                    gate_list_new.append((splicing_fragments_item[0], start_time,
                                                          start_time + fragment_second, f'{class_name}_大门'))
                                else:
                                    listt.append((splicing_fragments_item[0], start_time, start_time + fragment_second,
                                                  f'{class_name}_其他'))
                            if start_time + fragment_second > splicing_fragment_item[1]:
                                raise Exception("越界了！")
                    splicing_fragments_dict_new[class_name] = listt
                    remain_num = class_frame_num_dict[class_name] - len(listt) - len(gate_list_new)
                    # print(f"{class_name} 需要再填入自己{remain_num}个视频片段！")
                    if gate_list:
                        if gate_list_new:
                            splicing_fragments_dict_new[class_name] = gate_list_new + listt
                        else:
                            raise Exception("gate_list_new is empty!")
                        splicing_fragments_dict_new[class_name] += [
                            (video_path, 0, fragment_second, f"{class_name}_其他")
                            for video_path in
                            random.sample(class_video_dict[class_name]['其他'], remain_num)]  # 这里是remain_num个数的自己视频
                    else:
                        if remain_num:
                            splicing_fragments_dict_new[class_name].insert(0, (
                                random.choice(class_video_dict[class_name]['大门']), 0, fragment_second,
                                f"{class_name}_大门"))
                        else:
                            raise Exception("remain_num is 0 !")
                        if remain_num > 1:
                            splicing_fragments_dict_new[class_name] += [
                                (video_path, 0, fragment_second, f"{class_name}_其他")
                                for video_path in random.sample(class_video_dict[class_name]['其他'], remain_num - 1)]
                    already_processed.add(class_name)
                    # print(f"填入后 splicing_fragments_dict_new[{class_name}]：{splicing_fragments_dict_new[class_name]}")
                # else:
                #     # print(f"{class_name} 替换掉！")
                #     # if class_name not in extra_class_name_set:
                #     need_replace.add(class_name)
                #     del splicing_fragments_dict[class_name]
                # else:
                #     # 这里是要对片段进行分割的，均出来 1.只够自己 2.还可给别人
                #     pass
        else:
            if class_name not in extra_class_name_set:
                need_replace.add(class_name)
    replace_time_dict = {}
    multiple_time_dict = {}
    multiple_num_dict = {}

    # print("need_replace:", need_replace)
    remainder_class_name_set = all_class_name_set - set(class_name_list)
    # print("remainder_class_name_set:", remainder_class_name_set)
    if remainder_class_name_set:
        remainder_class_sorted = sorted(
            {i: class_name_dict[i][1] for i in remainder_class_name_set if i in class_name_dict}.items(),
            key=lambda x: x[1], reverse=False)
        if remainder_class_sorted:
            need_replace_sorted = sorted({i: class_frame_num_dict[i] for i in need_replace}.items(),
                                         key=lambda x: x[1], reverse=True)
            for class_name, need_frame_num in need_replace_sorted:
                for i in range(len(remainder_class_sorted) - 1, -1, -1):
                    if need_frame_num <= remainder_class_sorted[i][1]:
                        need_replace.discard(class_name)
                        for dictt in [splicing_fragments_dict, splicing_fragments_dict2, splicing_fragments_dict3,
                                      class_name_dict]:
                            if remainder_class_sorted[i][0] in dictt:
                                dictt[class_name] = dictt[remainder_class_sorted[i][0]]  # 直接改成需要被补充的类里面的内容了
                                del dictt[remainder_class_sorted[i][0]]
                        # splicing_fragments_dict[class_name]=splicing_fragments_dict[remainder_class_sorted[i][0]]
                        # del splicing_fragments_dict[remainder_class_sorted[i][0]]
                        del remainder_class_sorted[i]
                    else:
                        if need_frame_num <= class_name_dict[remainder_class_sorted[i][0]][2]:
                            need_replace.discard(class_name)
                            for dictt in [splicing_fragments_dict, splicing_fragments_dict2,
                                          splicing_fragments_dict3, class_name_dict]:
                                if remainder_class_sorted[i][0] in dictt:
                                    dictt[class_name] = dictt[remainder_class_sorted[i][0]]
                                    del dictt[remainder_class_sorted[i][0]]
                            # splicing_fragments_dict[class_name] = splicing_fragments_dict[
                            #     remainder_class_sorted[i][0]]
                            # del splicing_fragments_dict[remainder_class_sorted[i][0]]
                            del remainder_class_sorted[i]
        for class_name, _ in remainder_class_sorted:
            for dictt in [splicing_fragments_dict, splicing_fragments_dict2,
                          splicing_fragments_dict3, class_name_dict]:
                if class_name in dictt:
                    del dictt[class_name]
    # print("need_replace::", need_replace)
    # if need_replace:

    if need_replace:  # 可能存在 remainder_class_name 没有物尽其用   解决了
        for class_name in splicing_fragments_dict.keys():
            if already_processed:
                if class_name in already_processed:
                    continue
            if class_name in extra_class_name_set:
                continue
            if hierarchy_dict[class_name] == 1:
                all_time = class_name_dict[class_name][2]
                all_num = class_name_dict[class_name][1]
                if class_name in class_name_dict2:
                    all_time += class_name_dict2[class_name][2]
                    all_num += class_name_dict2[class_name][1]
                if class_name in class_name_dict3:
                    all_time += class_name_dict3[class_name][2]
                    all_num += class_name_dict3[class_name][1]
            elif hierarchy_dict[class_name] == 2:
                all_time = class_name_dict[class_name][2]
                all_num = class_name_dict[class_name][1]
                if class_name in class_name_dict3:
                    all_time += class_name_dict3[class_name][2]
                    all_num += class_name_dict3[class_name][1]
            else:
                all_time = class_name_dict[class_name][2]
                all_num = class_name_dict[class_name][1]
            if class_name not in remainder_class_name_set:
                # remainder_time = all_time - min_fragment_num
                # remainder_num = all_num - min_fragment_num
                # else:
                remainder_time = all_time - class_frame_num_dict[class_name]
                remainder_num = all_num - class_frame_num_dict[class_name]
                if remainder_time >= min_fragment_num:
                    multiple_time_dict[class_name] = remainder_time
                if remainder_num >= min_fragment_num:
                    multiple_num_dict[class_name] = remainder_num
        # print("multiple_time_dict:", multiple_time_dict)  # multiple_time_dict
        # print("multiple_num_dict:", multiple_num_dict)  # multiple_num_dict
        sorted_need_time_num, replace_time_dict = is_meet_need(copy.deepcopy(multiple_time_dict), need_replace,
                                                               class_frame_num_dict)
        # print("sorted_need_time_num:", sorted_need_time_num)
        # print("replace_time_dict:", replace_time_dict)
        if len(sorted_need_time_num) == 0:  # 片段时间满足了
            sorted_need_num_num, replace_num_dict = is_meet_need(copy.deepcopy(multiple_num_dict), need_replace,
                                                                 class_frame_num_dict)
            # print("sorted_need_num_num:", sorted_need_num_num)
            # print("replace_num_dict:", replace_num_dict)
            if len(sorted_need_num_num) == 0:  # 个数满足了
                # print("片段分出来就可以满足替换要求,只不过有些景点会重复出现两大段以上！")
                for class_name in splicing_fragments_dict.keys():
                    if already_processed:
                        if class_name in already_processed:
                            continue
                    if class_name in remainder_class_name_set:  # 干净了
                        del splicing_fragments_dict[class_name]
                        continue
                    # print(f"***{class_name}***")
                    temp_list = [(i[0], j[0], j[1], j[2]) for i in splicing_fragments_dict[class_name] for j in i[1]]
                    if class_name in replace_num_dict:
                        all_num_ = sum([i[1] for i in replace_num_dict[class_name]]) + class_frame_num_dict[
                            class_name]
                        if all_num_ > class_name_dict[class_name][1]:  # 可能是需要下几级补上额
                            temp_list = update_temp_list(temp_list, hierarchy_dict, class_name,
                                                         splicing_fragments_dict2,
                                                         splicing_fragments_dict3)
                        if len(temp_list) < all_num_:
                            raise Exception("temp_list长度不够！")
                        splicing_fragments_dict_new[class_name] = update_clazz_distribution(temp_list,
                                                                                            all_num_,
                                                                                            fragment_second)  #
                        # print(f"splicing_fragments_dict_new[{class_name}]:", splicing_fragments_dict_new[class_name])
                    else:
                        update_clazz_single_distribution(splicing_fragments_dict_new, class_name, class_name_dict,
                                                         class_frame_num_dict[class_name], temp_list,
                                                         fragment_interval_second, fragment_second)
                # distribution_master_list = adjust_position(class_frame_num_dict, class_name_list,extra_class_name_set,
                #                                            splicing_fragments_dict,
                #                                            replace_num_dict)
            else:
                # print("时间上切分一下就可以满足替换要求,只不过有些景点会重复出现两大段以上！")
                allocation_by_time(replace_time_dict, multiple_time_dict, class_frame_num_dict,
                                   splicing_fragments_dict, splicing_fragments_dict_new,
                                   already_processed, remainder_class_name_set,
                                   multiple_num_dict, class_name_dict, hierarchy_dict,
                                   splicing_fragments_dict2,
                                   splicing_fragments_dict3, fragment_interval_second, fragment_second)

        else:
            # print("连分出来都弥补不了！", "还差", len(sorted_need_time_num))
            for class_name, fragment_num in sorted_need_time_num:
                random_video = random.choice(class_video_dict[class_name]['大门'])
                material_included_list.append(random_video)
                splicing_fragments_dict_new[class_name] = [(random_video, 0, fragment_second, f"{class_name}_大门")]
                if fragment_num > 1:
                    splicing_fragments_dict_new[class_name] += [(video_path, 0, fragment_second, f"{class_name}_其他")
                                                                for video_path in
                                                                random.sample(class_video_dict[class_name]['其他'],
                                                                              fragment_num - 1)]  # 填入自己的视频
                already_processed.add(class_name)
                # print(f"splicing_fragments_dict_new[{class_name}]:", splicing_fragments_dict_new[class_name])
            if replace_time_dict:
                # print("replace_time_dict:")
                allocation_by_time(replace_time_dict, multiple_time_dict, class_frame_num_dict,
                                   splicing_fragments_dict, splicing_fragments_dict_new,
                                   already_processed, remainder_class_name_set,
                                   multiple_num_dict, class_name_dict, hierarchy_dict,
                                   splicing_fragments_dict2,
                                   splicing_fragments_dict3, fragment_interval_second, fragment_second)

            else:
                # print("internal_single_assignment:")
                internal_single_assignment(splicing_fragments_dict, splicing_fragments_dict_new, already_processed,
                                           class_name_dict,
                                           class_frame_num_dict,
                                           fragment_interval_second, fragment_second, remainder_class_name_set)

    else:
        # print("internal_single_assignment2:")
        internal_single_assignment(splicing_fragments_dict, splicing_fragments_dict_new, already_processed,
                                   class_name_dict,
                                   class_frame_num_dict,
                                   fragment_interval_second, fragment_second, remainder_class_name_set)
        # distribution_master_list = [splicing_fragments_dict_new[class_name] for class_name in class_name_list]
    # else:
    #     # print("internal_single_assignment3:")
    #     internal_single_assignment(splicing_fragments_dict,splicing_fragments_dict_new, already_processed, class_name_dict, class_frame_num_dict,
    #                                fragment_interval_second, fragment_second)
    #     # distribution_master_list = [splicing_fragments_dict_new[class_name] for class_name in class_name_list]
    distribution_master_list = adjust_position(class_frame_num_dict, class_name_list, extra_class_name_set,
                                               splicing_fragments_dict, splicing_fragments_dict_new,
                                               replace_time_dict,
                                               multiple_num_dict, multiple_time_dict, class_name_dict,
                                               hierarchy_dict, splicing_fragments_dict2,
                                               splicing_fragments_dict3, fragment_second,
                                               fragment_interval_second, class_video_dict)
    # # print("distribution_master_list:", distribution_master_list)
    # connection_process_list = [[(i[0], gen_time_str(i[1]), gen_time_str(i[2])) for i in item] for item in
    #                            distribution_master_list]
    # return splicing_fragments_dict
    return distribution_master_list, material_included_list


def frame2time(clip_process_list_, frame_rate=30):
    clip_process_list = []
    for clip_process_sub_ in clip_process_list_:
        clip_process_sub = []
        for clip_process in clip_process_sub_:
            clip_split = clip_process[0].split(':')
            clip_process_sub.append(
                (int(clip_split[0]) + int(clip_split[1]) / frame_rate, clip_process[1], clip_process[2] / frame_rate))
        clip_process_list.append(clip_process_sub)
    return clip_process_list


def splicing_transition_fragments(total_list, video_index_dict, transition_start_index, ind, concat_clip_index,
                                  transition_str_list, concat_list):
    front_part = total_list[transition_start_index]  # 1
    offset = front_part[0] - front_part[2]
    transition = front_part[1]
    duration = str(front_part[2])
    cmd_str = f'[{video_index_dict[transition_start_index]}][{video_index_dict[transition_start_index + 1]}]xfade=transition={transition}:duration={duration}:offset={str(offset)},format=yuv420p,setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1[temp]'
    for i in range(transition_start_index + 1, ind):
        front_part = total_list[i]
        offset += front_part[0] - front_part[2]
        transition = front_part[1]
        duration = str(front_part[2])
        cmd_str += f";[temp][{video_index_dict[i + 1]}]xfade=transition={transition}:duration={duration}:offset={str(offset)},format=yuv420p,setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1[temp]"
    concat_clip_index_str = f"[v{str(concat_clip_index)}]"
    cmd_str = cmd_str[:-6] + concat_clip_index_str
    transition_str_list.append(cmd_str)
    concat_list.append(concat_clip_index_str)


def fragments_compose(total_list, video_index_dict, audio_index, cmd_str_all, video_dir, save_dir, video_name,
                      fast_cmd=None):  # total_list=clip_process_list[inde]  #fast_cmd=-r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M
    # inde = int(index1) + 1
    transition_start_index = None
    concat_list = []
    concat_clip_index = 0
    transition_str_list = []
    # len_ = len(clip_process_list[inde])
    len_ = len(total_list)
    for ind in range(len_ - 1):
        # if final_phase:
        #     transition_ = total_list[ind][-1][1]
        # else:
        transition_ = total_list[ind][1]
        if transition_ == None:
            if transition_start_index != None:

                splicing_transition_fragments(total_list, video_index_dict, transition_start_index, ind,
                                              concat_clip_index, transition_str_list, concat_list)
                concat_clip_index += 1
                transition_start_index = None
                # if ind == len_ - 2:
                #     concat_list.append(f"[{str(ind+1)}]")
            else:
                # concat_list.append(f"[{str(ind)}]")
                concat_list.append(f"[{video_index_dict[ind]}]")
                # if ind == len_ - 2:
                #     concat_list.append(f"[{str(ind+1)}]")
            if ind == len_ - 2:
                # concat_list.append(f"[{str(ind + 1)}]")
                concat_list.append(f"[{video_index_dict[ind + 1]}]")
        else:
            if transition_start_index == None:
                transition_start_index = ind
                # if ind == len_ - 2:
                #     splicing_transition_fragments(final_phase,total_list, transition_start_index, ind+1,
                #                                   concat_clip_index, transition_str_list, concat_list)
            # elif ind == len_ - 2:
            #     splicing_transition_fragments(final_phase,total_list, transition_start_index, ind+1, concat_clip_index,
            #                                   transition_str_list, concat_list)
            if ind == len_ - 2:
                splicing_transition_fragments(total_list, video_index_dict, transition_start_index, ind + 1,
                                              concat_clip_index,
                                              transition_str_list, concat_list)
    # print("concat_list:", concat_list)
    # print("transition_str_list:", transition_str_list)
    # cmd_str_all = f"""ffmpeg {' '.join(['-i ' + video_dir + '/' + save_dir + '/' + index1 + '_' + str(i) + '.mp4' for i in range(length)])} -filter_complex " """
    cmd_str_all += ';'.join(transition_str_list)
    if len(concat_list) == 1:
        if '[v' in concat_list[0]:
            cmd_str_all = cmd_str_all.split('[v')[0]
            cmd_str_all += f""" " {fast_cmd if fast_cmd else ''}-y {video_dir}/{save_dir}/{video_name}.mp4 -hide_banner -loglevel error"""
            # print(cmd_str_all)
            result = subprocess.call(cmd_str_all, shell=True)
    else:
        cmd_str_all += f""";{''.join(concat_list)}concat=n={str(len(concat_list))}[finally];[{audio_index}:a]aloop=loop=1[a1]" -map "[finally]" -map "[a1]" {fast_cmd if fast_cmd else ''}-y {video_dir}/{save_dir}/{video_name}.mp4 -hide_banner -loglevel error"""
        # print(cmd_str_all)
        result = subprocess.call(cmd_str_all, shell=True)
    return result


def ffmpeg_procedure(connection_process_list, clip_process_list, video_dir, template_video_dir, surplus_num,
                     video_path_list, material_included_list,
                     save_dir='save', scale="1920:1080", photo_scale="768x440", fps='30',
                     color="white", alpha="0.6", thickness="15", single_time=2, front_second=2):  #
    # scale="1920:1080";fps='30';photo_scale = "768*440";color = "white";alpha = "0.6";thickness = "15";single_time = 2
    # print("ffmpeg_procedure!!!")
    start_time = time.time()
    # cmd_str_format = "ffmpeg -y -i %s -ss %s -t %s -s %s -an -vcodec libx264 -keyint_min 2 -g 1 -r %s -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y %s  -hide_banner -loglevel error"
    # cmd_str_format = "ffmpeg -hwaccel cuda -c:v h264_cuvid -y -i %s -ss %s -t %s -vf scale=%s,setsar=sar=1/1 -an -keyint_min 2 -g 1  -c:v h264_nvenc -r %s -crf 28  -b:v 2M -bufsize 2M -y %s  -hide_banner -loglevel error"
    # cmd_str_format = "{ffmpeg_path} -y -i %s -ss %s -t %s -vf scale=%s,setsar=sar=1/1 -an -vcodec libx264 -keyint_min 2 -g 1 -r %s -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y %s  -hide_banner -loglevel error"
    # cmd_str_format = "ffmpeg -y -i %s -ss %s -t %s -vf scale=%s,setsar=sar=1/1 -an -keyint_min 2 -g 1 -c:v h264_nvenc -r %s -crf 28  -b:v 2M -bufsize 2M -y %s  -hide_banner -loglevel error"

    #     index_jpg = 0
    #     class_num_ = len(connection_process_list)
    #     jpg_need_index = 5
    #     while index_jpg <= jpg_need_index:
    #         # print(f"[{index_jpg % class_num_}][{index_jpg // class_num_}]")
    #         connection_process = connection_process_list[index_jpg % class_num_][index_jpg // class_num_]
    #         subprocess.call(
    #             f"""{ffmpeg_path} -i {connection_process[0]} -ss {connection_process[1] + 1} -frames:v 1 -vf "scale={photo_scale},drawbox=x=0:y=0:w=iw:h=ih:color={color}@{alpha}:t={thickness}" -y {video_dir}/{save_dir}/{str(index_jpg)}.jpg -hide_banner -loglevel error""",
    #             shell=True)
    #         index_jpg += 1
    #
    #     existed = False
    #     while not existed:
    #         existed = True
    #         for i in range(jpg_need_index + 1):
    #             if not os.path.exists(f"{video_dir}/{save_dir}/{str(i)}.jpg"):
    #                 existed = False
    #     # print('抽取图片：' + str(time.time() - start_time) + '秒')  # 15.8
    #     d2 = str(0.6 * single_time)
    #     last_remain_second = clip_process_list[-1][0][0] - front_second - single_time * (jpg_need_index + 1)
    #     end_clip_process_list = [(second_, None, 0) for second_ in
    #                              [front_second] + [single_time for i in range(6)] + [last_remain_second]]
    #     last_remain_second = str(last_remain_second)
    #     single_time = str(single_time)
    #     front_second = str(front_second)
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg -t {front_second} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_0.mp4 -hide_banner -loglevel error""",
    #         shell=True)
    #     # 第0-1秒
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(1)])} -filter_complex
    #     "[1:v]scale={photo_scale},rotate='45*PI/180-60*PI/180*t/{single_time}:ow=hypot(iw,ih):oh=ow:c=0x00000000',fade=in:st=0:d={single_time}:alpha=1[v1];
    #     [0][v1]overlay=x='-t*W/8/{single_time}+(W-w)/2':y=(H-h)/2"
    #     -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_1.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""), shell=True)
    #     # 第1-2秒
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(2)])} -filter_complex
    #     "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
    #     [0][v1]overlay=x='-t*W/8/{single_time}+3*W/8-w/2':y=(H-h)/2[over1];
    #     [2:v]scale={photo_scale},rotate='15*PI/180*t/{single_time}:ow=hypot(iw,ih):oh=ow:c=0x00000000',fade=in:st=0:d={d2}:alpha=1[v2];
    #     [over1][v2]overlay=y='-t*H/8/{single_time}+(H-h)/2':x='(W-w)/2-w/8*t/{single_time}'"
    #     -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_2.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""), shell=True)
    #     # 第2-3秒
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(3)])} -filter_complex
    #     "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
    #     [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
    #     [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
    #     [over1][v2]overlay=y='-t*H/8/{single_time}+(H-h)/2-H/8':x='(W-w)/2-w/8*t/{single_time}-w/8'[over2];
    #     [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
    #     [over2][v3]overlay=y='t*(H/2-h/4)/{single_time}+(H-h)/2':x='W+w/2-(W/4+w*5/8)*t/{single_time}'"
    #     -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_3.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""), shell=True)
    #     # 第3-4秒
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(4)])} -filter_complex
    #     "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
    #     [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
    #     [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
    #     [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
    #     [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
    #     [over2][v3]overlay=y='H-3*h/4':x='W*3/4-w/8-(W/4+w*5/8)*t/{single_time}'[over3];
    #     [4:v]scale={photo_scale},rotate='if(lte(t,0.5),0,-13*PI/180*t/{single_time}+6*PI/180):ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
    #     [over3][v4]overlay=x='-t*(W/8+w/2)/{single_time}+W+w/2':y='(H-h)/2-h/8*t/{single_time}'"
    #     -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_4.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""),
    #         shell=True)  # W*15/16+w/4
    #     # 第4-5秒
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(5)])} -filter_complex
    #     "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
    #     [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
    #     [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
    #     [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
    #     [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
    #     [over2][v3]overlay=y='H-3*h/4':x='W/2-3*w/4'[over3];
    #     [4:v]scale={photo_scale},rotate='-13*PI/180*t/{single_time}-7*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
    #     [over3][v4]overlay=x='-t*(W/8+w/2)/{single_time}+W*7/8':y='H/2-h*5/8-h/8*t/{single_time}'[over4];
    #     [5:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v5];
    #     [over4][v5]overlay=x='(3*W/4-w/2)':y='(H+h)/2-5*h/16*t/{single_time}'"
    #     -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_5.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""), shell=True)
    #     # 第5-6秒
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(6)])} -filter_complex
    #     "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
    #     [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
    #     [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
    #     [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
    #     [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
    #     [over2][v3]overlay=y='H-3*h/4':x='W/2-3*w/4'[over3];
    #     [4:v]scale={photo_scale},rotate='-20*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
    #     [over3][v4]overlay=x='3*W/4-w/2':y='H/2-3*h/4'[over4];
    #     [5:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v5];
    #     [over4][v5]overlay=x='(3*W/4-w/2)':y='H/2+h*3/16-5*h/16*t/{single_time}'[over5];
    #     [over5][6]overlay=y='(H-h)/2':x='(W/2-w/4)*t/{single_time}'"
    #     -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_6.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""), shell=True)
    #     # last
    #     subprocess.call(
    #         f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(6)])} -filter_complex
    # "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
    # [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
    # [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
    # [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
    # [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
    # [over2][v3]overlay=y='H-3*h/4':x='W/2-3*w/4'[over3];
    # [4:v]scale={photo_scale},rotate='-20*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
    # [over3][v4]overlay=x='3*W/4-w/2':y='H/2-3*h/4'[over4];
    # [5:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v5];
    # [over4][v5]overlay=x='(3*W/4-w/2)':y='H/2-h/8'[over5];
    # [over5][6]overlay=y='(H-h)/2':x='W/2-w/4'"
    #         -t {last_remain_second} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_7.mp4  -hide_banner -loglevel error""".replace(
    #             "\n", ""),
    #         shell=True)
    #     # print('生成相册：' + str(time.time() - start_time) + '秒')  # 29.5

    # cmd_str_all = f"ffmpeg -c:v h264_cuvid -i {template_video_dir}/0x.mp4 "
    last_remain_second = clip_process_list[-1][0][0] - front_second - single_time * 6
    if surplus_num:
        # if surplus_num>3:
        #     pass
        # else:
        material_list = [(i[0][0], i[0][1]) for i in connection_process_list if i[0][0].split('/')[-2] != 'upload']
        # print(material_list)
        # material_list=[(j[0],j[1]) for i in connection_process_list for j in i if j[0].split('/')[-2]!='upload']
        if len(material_list) >= surplus_num:
            material_list = material_list[:surplus_num]
            jpg_input_list = [video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(6 - surplus_num)] + [
                os.path.splitext(i[0])[0] + '.jpg' for i in material_list]
        else:
            jpg_input_list = [video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(6 - surplus_num)] + [
                os.path.splitext(i[0])[0] + '.jpg' for i in material_list]
            surplus_num_ = surplus_num - len(material_list)
            material_add_list = [(i[-1][0], i[-1][1]) for i in connection_process_list if
                                 i[0][0].split('/')[-2] == 'upload'][:surplus_num_]
            resultt_list = [subprocess.call(
                f"""{ffmpeg_path} -i {material_item[0]} -ss {material_item[1] + 1} -frames:v 1 -vf "scale={photo_scale},drawbox=x=0:y=0:w=iw:h=ih:color={color}@{alpha}:t={thickness}" -y {video_dir}/{save_dir}/add_{str(index)}.jpg -hide_banner -loglevel error""",
                shell=True) for index, material_item in enumerate(material_add_list)]
            jpg_input_list += [video_dir + '/' + save_dir + '/add_' + str(i) + '.jpg' for i in
                               range(len(material_add_list))]
        # print("jpg_input_list:", jpg_input_list)
        # resultt_list=[]
        having_pic_num = 6 - surplus_num
        # for index,material_item in enumerate(material_list):
        #     resultt=subprocess.call(
        #                 f"""{ffmpeg_path} -i {material_item[0]} -ss {material_item[1] + 1} -frames:v 1 -vf "scale={photo_scale},drawbox=x=0:y=0:w=iw:h=ih:color={color}@{alpha}:t={thickness}" -y {video_dir}/{save_dir}/{str(index + having_pic_num)}.jpg -hide_banner -loglevel error""",
        #                 shell=True)
        #     resultt_list.append(resultt)
        d2 = str(0.6 * single_time)
        # last_remain_second = clip_process_list[-1][0][0] - front_second - single_time * 6
        # last_remain_second = str(last_remain_second)
        single_time = str(single_time)
        for i in range(having_pic_num + 1, 7):
            # while sum(resultt_list[:i-having_pic_num]) != 0:
            #     # print(sum(resultt_list[:i]))
            #     pass
            while True:
                # jpg_path=f'{video_dir}/save/{str(i-1)}.jpg'
                jpg_path = jpg_input_list[i - 1]
                if os.path.exists(jpg_path):
                    if os.stat(jpg_path).st_size != 0:
                        # print('alrready exist!!')
                        break
            # if i == 2:
            #     end_2(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, d2,jpg_input_list)
            # elif i < 6:
            #     exec(f"end_{i}(template_video_dir,photo_scale,single_time,fps,video_dir,save_dir,jpg_input_list)")
            # else:
            #     end_6(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir,jpg_input_list)
            #     end_7(template_video_dir, photo_scale, str(last_remain_second), fps, video_dir, save_dir,jpg_input_list)
            if i == 2:
                result = end_2(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, d2,
                               jpg_input_list)
                while result:
                    result = end_2(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, d2,
                                   jpg_input_list)
            elif i < 6:
                exec(f"""result=end_{str(i)}(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir,jpg_input_list)
while result:
    result = end_{str(i)}(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir,jpg_input_list)
        """)
            elif i == 6:
                result = end_6(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, jpg_input_list)
                while result:
                    result = end_6(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir,
                                   jpg_input_list)
                result = end_7(template_video_dir, photo_scale, str(last_remain_second), fps, video_dir, save_dir,
                               jpg_input_list)
                while result:
                    result = end_7(template_video_dir, photo_scale, str(last_remain_second), fps, video_dir, save_dir,
                                   jpg_input_list)
            else:
                raise Exception("i>6!!!!")
    # else:
    #     last_remain_second = clip_process_list[-1][0][0] - front_second - single_time * 6
    end_exist = False
    while not end_exist:
        end_exist = True
        for i in range(1, 8):
            end_video_path = f"{video_dir}/{save_dir}/end_{str(i)}.mp4"
            if not os.path.exists(end_video_path):
                end_exist = False
            else:
                if os.stat(end_video_path).st_size == 0:
                    end_exist = False
                else:
                    log_path = f"{video_dir}/{save_dir}/error.log"
                    result = subprocess.call(f'{ffmpeg_path} -v error -i {end_video_path} -f null - 2>{log_path}',
                                             shell=True)
                    if result == 0:
                        if os.path.exists(log_path):
                            if os.stat(log_path).st_size != 0:
                                # print("os.stat(log_path).st_size:", os.stat(log_path).st_size)
                                end_exist = False
                        else:
                            # print(f"{log_path} not exist!!")
                            end_exist = False
                    else:
                        # print("result:", result)
                        end_exist = False
    # video_exist = False
    # while not video_exist:
    #     video_exist = True
    #     for video_path in video_path_list:
    #         if not os.path.exists(video_path):
    #             video_exist = False
    #         else:
    #             if os.stat(video_path).st_size == 0:
    #                 video_exist = False
    #             else:
    #                 log_path = f"{video_dir}/{save_dir}/error2.log"
    #                 result = subprocess.call(f'{ffmpeg_path} -v error -i {video_path} -f null - 2>{log_path}',
    #                                          shell=True)
    #                 if result == 0:
    #                     if os.path.exists(log_path):
    #                         if os.stat(log_path).st_size != 0:
    #                             # print("os.stat(log_path).st_size:", os.stat(log_path).st_size)
    #                             video_exist = False
    #                     else:
    #                         # print(f"{log_path} not exist!!")
    #                         video_exist = False
    #                 else:
    #                     # print("result:", result)
    #                     video_exist = False

    # trans_video_exist = False
    # while not trans_video_exist:
    #     trans_video_exist = True
    #     for video_path in video_path_list:
    #         if not os.path.exists(video_path):
    #             # print(video_path+' not exist!')
    #             trans_video_exist = False
    # print('生成相册：' + str(time.time() - start_time) + '秒')  # 29.5
    video_index_list = []
    connection_transformation_list = []
    for index1, connection_process_sub in enumerate(connection_process_list):
        for index2, connection_process in enumerate(connection_process_sub):
            if connection_process[0] in video_index_list:
                video_index = video_index_list.index(connection_process[0])
            else:
                video_index = len(video_index_list)
                video_index_list.append(connection_process[0])
            start_frame_index = round(connection_process[1] * 30)
            end_frame_index = start_frame_index + round(clip_process_list[index1 + 1][index2][0] * 30) - 1
            connection_transformation_list.append((video_index + 1, start_frame_index, end_frame_index))
    # print("video_index_list:", video_index_list)
    # print("connection_transformation_list:", connection_transformation_list)

    # last_remain_second = clip_process_list[-1][0][0] - front_second - int(single_time) * 6
    end_clip_process_list = [(second_, None, 0) for second_ in
                             [front_second] + [single_time for i in range(6)] + [last_remain_second]]
    # 对照
    # [round(j[0]*30) for i in clip_process_list[1:-1] for j in i]
    # [i[2]-i[1] for i in connection_transformation_list]
    # [round(int(j[0].split(":")[0])*30+int(j[0].split(":")[1])) for i in clip_process_list_[1:-1] for j in i]
    clip_process_straighten_list = [clip_process for clip_process_sub in clip_process_list[:-1] for clip_process in
                                    clip_process_sub]
    # connection_process_len=sum([len(i) for i in connection_process_list])
    connection_process_len = len(clip_process_straighten_list)
    end_index_start = len(video_index_list) + 1
    # video_index_dict={**{0:'t0'},**{i:f'ct{str(i)}' for i in range(1,connection_process_len)},**{connection_process_len+i:f't{str(end_index_start + i)}' for i in range(8)}}
    video_index_dict = {**{0: 't0'}, **{i: f'ct{str(i)}' for i in range(1, connection_process_len)},
                        **{connection_process_len + i: f't{str(end_index_start + i)}' for i in range(8)}}
    # video_index_dict[0]='0'
    clip_process_straighten_list += end_clip_process_list
    cmd_str_all = f"{ffmpeg_path} -i {template_video_dir}/0x.mp4 -i "
    cmd_str_all += ' -i '.join(video_index_list)
    cmd_str_all += f' -i {template_video_dir}/end_0.mp4 '
    # cmd_str_all += ' '.join(
    #     [f'-i {video_dir}/{save_dir}/{str(index1)}_{str(index2)}.mp4' for index1,clip_process_sub in enumerate(clip_process_list[1:-1]) for index2,clip_process in enumerate(clip_process_sub)])
    cmd_str_all += ''.join([f' -i {video_dir}/{save_dir}/end_{str(i)}.mp4' for i in range(1, 8)])
    cmd_str_all += f' -i {template_video_dir}/bg.mp3 -filter_complex "'
    # cmd_str_all += f' -i {video_dir}/{save_dir}/end.mp4 -i {template_video_dir}/bg.mp3 -filter_complex " '
    audio_index = end_index_start + 8
    cmd_str_all += '[0]setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1[t0];'
    # cmd_str_all+=''.join([f"[{i}]settb=AVTB[t{i}];" for i in range(audio_index)])
    cmd_str_all += ''.join(
        [f"[{str(end_index_start + i)}]setpts=N/FRAME_RATE/TB,settb=AVTB,setsar=sar=1/1[t{str(end_index_start + i)}];"
         for i in range(8)])
    cmd_str_all += ''.join([
        f"[{ct[0]}]select='between(n,{ct[1]},{ct[2]})',setpts=N/FRAME_RATE/TB,scale={scale},settb=AVTB,setsar=sar=1/1 [ct{str(index + 1)}];"
        for index, ct in enumerate(connection_transformation_list)])

    result = fragments_compose(clip_process_straighten_list, video_index_dict, audio_index, cmd_str_all, video_dir,
                               save_dir, video_name="ai_composite",
                               # final_phase=True, fast_cmd=f'-acodec copy -r {fps} -preset medium -b:v 2M -bufsize 2M ')
                               fast_cmd=f' -c:v h264_nvenc -r {fps} -preset medium -b:v 2M -bufsize 2M ')
    while not os.path.exists(f"{video_dir}/{save_dir}/ai_composite.mp4"):
        pass
    # print('生成视频：' + str(time.time() - start_time) + '秒')
    # for i in range(6):
    #     os.remove(f"{video_dir}/{save_dir}/{str(i)}.jpg")
    # for i in range(8):
    #     os.remove(f"{video_dir}/{save_dir}/end_{str(i)}.mp4")
    # os.remove(f"{video_dir}/{save_dir}/end.mp4")
    # for index1, connection_process_sub in enumerate(connection_process_list):
    #     for index2, connection_process in enumerate(connection_process_sub):
    #         os.remove(f"{video_dir}/{save_dir}/{str(index1)}_{str(index2)}.mp4")
    # for i in range(len(connection_process_list)):
    #     os.remove(f"{video_dir}/{save_dir}/{str(i)}.mp4")
    # print("over!")
    return result


def analysis_checkpoint(original_checkpoint_list):
    def str2fps(strf):
        strf_split = strf.split(':')
        if len(strf_split) == 2:
            f_num = int(strf_split[0]) * 30 + int(strf_split[1])
        elif len(strf_split) == 3:
            f_num = int(strf_split[0]) * 60 * 30 + int(strf_split[1]) * 30 + int(strf_split[2])
        return f_num

    def fps2str(fps):
        return str(int(fps) // 30) + ':' + str(int(fps) % 30).rjust(2, '0')

    clip_process_list_ = []
    for index1, original_checkpoint_sub in enumerate(original_checkpoint_list):
        clip_process_sub = []
        for index2, (original_checkpoint, transition) in enumerate(original_checkpoint_sub):
            str1, str2 = original_checkpoint.split(" ")
            str11, str12 = str1.split("-")
            # f11 = str2fps(str11) if str11 else str2fps(str12) - 1
            f11 = str2fps(str11) if str11 else str2fps(str12)
            str21, str22 = str2.split("-")
            f22 = str2fps(str22)
            clip_process_sub.append((fps2str(f22 - f11), transition, f22 - str2fps(str21) if str21 else 0))
        clip_process_list_.append(clip_process_sub)
    return clip_process_list_


def load_json(json_path):
    # json_path=os.path.splitext(video_path)[0][:-1]+ '.json'
    while not os.path.exists(json_path):
        # raise Exception(f'{json_path} 不存在！')
        # # print(f"{json_path} not exist!!!!!")
        pass
    with open(json_path, 'r', encoding='utf-8') as f:
        recognized_fragments = json.load(f)
    return recognized_fragments


def whole_process(video_dir, material_video_dir, template_video_dir,
                  class_frame_num_dict, extra_class_name_set, original_checkpoint_list,
                  surplus_num, fragment_interval_second=2,
                  scale="1920:1080", photo_scale="768x440", single_time=2, front_second=2,
                  # idx_to_class={0: '中天楼', 1: '华光楼', 2: '川北道署', 3: '张飞庙', 4: '文庙', 5: '贡院'},
                  idx_to_class={0: '中天楼_其他', 1: '中天楼_大门', 2: '华光楼_其他', 3: '华光楼_大门',
                                4: '川北道署_其他', 5: '川北道署_大门', 6: '张飞庙_其他', 7: '张飞庙_大门',
                                8: '文庙_其他', 9: '文庙_大门', 10: '牌坊', 11: '街景', 12: '贡院_其他',
                                13: '贡院_大门'},
                  model_path='model_ft3.pth',
                  device="cuda:0"):
    start_time = time.time()
    all_file_net_list = []
    for file in glob.glob(f'{video_dir}/upload/*.*'):
        file_name = os.path.splitext(os.path.basename(file))[0]
        if file_name[-1] == '#':
            file_name = file_name[:-1]
        all_file_net_list.append(file_name)
    all_file_net_set = set(all_file_net_list)
    all_exist_ = False
    while not all_exist_:
        all_exist_ = True
        for file_net in all_file_net_set:
            if not os.path.exists(f'{video_dir}/upload/{file_net}.json'):
                all_exist_ = False
                # break
    json_path_list = glob.glob(f'{video_dir}/upload/*.json')

    video_path_list = [os.path.splitext(json_path)[0] + '#.mp4' for json_path in json_path_list]  # 用户视频
    class_video_dict = {c: {'大门': glob.glob(f"{material_video_dir}/{c}/大门/*.mp4"),
                            '其他': glob.glob(f"{material_video_dir}/{c}/其他/*.mp4")} for c in class_frame_num_dict if
                        c not in extra_class_name_set}  # 素材库
    class_video_dict.update({c: glob.glob(f"{material_video_dir}/{c}/*.mp4") for c in extra_class_name_set})
    recognized_fragments_list = [load_json(json_path) for json_path in json_path_list]
    clip_process_list_ = analysis_checkpoint(original_checkpoint_list)
    clip_process_list = frame2time(clip_process_list_, frame_rate=30)
    fragment_second = max([j[0] for i in clip_process_list[1:-1] for j in i]) + 0.1
    connection_process_list, material_included_list = distribution_procedure(video_path_list, recognized_fragments_list,
                                                                             class_video_dict,
                                                                             class_frame_num_dict, extra_class_name_set,
                                                                             fragment_second=fragment_second,
                                                                             fragment_interval_second=fragment_interval_second)
    result = ffmpeg_procedure(connection_process_list, clip_process_list, video_dir, template_video_dir, surplus_num,
                              video_path_list, material_included_list,
                              scale=scale, photo_scale=photo_scale, single_time=single_time, front_second=front_second)
    return result


def end_0(template_video_dir, front_second, fps, video_dir, save_dir):
    # print('end_0')  #
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg -t {front_second} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_0.mp4 -hide_banner -loglevel error""",
        shell=True)
    return result


def end_1(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, jpg_list=None):
    # print('end_1')
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(1)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        # result=os.system(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                        "[1:v]scale={photo_scale},rotate='45*PI/180-60*PI/180*t/{single_time}:ow=hypot(iw,ih):oh=ow:c=0x00000000',fade=in:st=0:d={single_time}:alpha=1[v1];
                        [0][v1]overlay=x='-t*W/8/{single_time}+(W-w)/2':y='(H-h)/2'" 
                        -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_1.mp4  -hide_banner -loglevel error""".replace(
            "\n", "")
        # )
        , shell=True)
    return result


def end_2(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, d2, jpg_list=None):
    # print('end_2')
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(2)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                        "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
                        [0][v1]overlay=x='-t*W/8/{single_time}+3*W/8-w/2':y=(H-h)/2[over1];
                        [2:v]scale={photo_scale},rotate='15*PI/180*t/{single_time}:ow=hypot(iw,ih):oh=ow:c=0x00000000',fade=in:st=0:d={d2}:alpha=1[v2];
                        [over1][v2]overlay=y='-t*H/8/{single_time}+(H-h)/2':x='(W-w)/2-w/8*t/{single_time}'" 
                        -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_2.mp4  -hide_banner -loglevel error""".replace(
            "\n", ""), shell=True)
    return result


def end_3(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, jpg_list=None):
    # print('end_3')
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(3)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                        "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
                        [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
                        [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
                        [over1][v2]overlay=y='-t*H/8/{single_time}+(H-h)/2-H/8':x='(W-w)/2-w/8*t/{single_time}-w/8'[over2];
                        [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
                        [over2][v3]overlay=y='t*(H/2-h/4)/{single_time}+(H-h)/2':x='W+w/2-(W/4+w*5/8)*t/{single_time}'" 
                        -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_3.mp4  -hide_banner -loglevel error""".replace(
            "\n", ""), shell=True)
    return result


def end_4(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, jpg_list=None):
    # print('end_4')
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(4)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                        "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
                        [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
                        [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
                        [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
                        [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
                        [over2][v3]overlay=y='H-3*h/4':x='W*3/4-w/8-(W/4+w*5/8)*t/{single_time}'[over3];
                        [4:v]scale={photo_scale},rotate='if(lte(t,0.5),0,-13*PI/180*t/{single_time}+6*PI/180):ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
                        [over3][v4]overlay=x='-t*(W/8+w/2)/{single_time}+W+w/2':y='(H-h)/2-h/8*t/{single_time}'" 
                        -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_4.mp4  -hide_banner -loglevel error""".replace(
            "\n", ""),
        shell=True)  # W*15/16+w/4
    return result


def end_5(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, jpg_list=None):
    # print('end_5')
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(5)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                        "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
                        [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
                        [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
                        [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
                        [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
                        [over2][v3]overlay=y='H-3*h/4':x='W/2-3*w/4'[over3];
                        [4:v]scale={photo_scale},rotate='-13*PI/180*t/{single_time}-7*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
                        [over3][v4]overlay=x='-t*(W/8+w/2)/{single_time}+W*7/8':y='H/2-h*5/8-h/8*t/{single_time}'[over4]; 
                        [5:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v5];
                        [over4][v5]overlay=x='(3*W/4-w/2)':y='(H+h)/2-5*h/16*t/{single_time}'" 
                        -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_5.mp4  -hide_banner -loglevel error""".replace(
            "\n", ""), shell=True)
    return result


def end_6(template_video_dir, photo_scale, single_time, fps, video_dir, save_dir, jpg_list=None):
    # print("end_6")
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(6)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                        "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
                        [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
                        [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
                        [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
                        [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
                        [over2][v3]overlay=y='H-3*h/4':x='W/2-3*w/4'[over3];
                        [4:v]scale={photo_scale},rotate='-20*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
                        [over3][v4]overlay=x='3*W/4-w/2':y='H/2-3*h/4'[over4]; 
                        [5:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v5];
                        [over4][v5]overlay=x='(3*W/4-w/2)':y='H/2+h*3/16-5*h/16*t/{single_time}'[over5];
                        [over5][6]overlay=y='(H-h)/2':x='(W/2-w/4)*t/{single_time}'" 
                        -t {single_time} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_6.mp4  -hide_banner -loglevel error""".replace(
            "\n", ""), shell=True)
    return result


def end_7(template_video_dir, photo_scale, last_remain_second, fps, video_dir, save_dir, jpg_list=None):
    # print("end_7")
    if jpg_list == None:
        jpg_input_str = ' '.join(['-loop 1 -i ' + video_dir + '/' + save_dir + '/' + str(i) + '.jpg' for i in range(6)])
    else:
        jpg_input_str = ' '.join(['-loop 1 -i ' + i for i in jpg_list])
    result = subprocess.call(
        f"""{ffmpeg_path} -loop 1 -i {template_video_dir}/bg.jpg {jpg_input_str} -filter_complex 
                    "[1:v]scale={photo_scale},rotate='-15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v1];
                    [0][v1]overlay=x='W/4-w/2':y=(H-h)/2[over1];
                    [2:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v2];
                    [over1][v2]overlay=y='H/4-h/2':x='W/2-3*w/4'[over2];
                    [3:v]scale={photo_scale},rotate='-30*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v3];
                    [over2][v3]overlay=y='H-3*h/4':x='W/2-3*w/4'[over3];
                    [4:v]scale={photo_scale},rotate='-20*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v4];
                    [over3][v4]overlay=x='3*W/4-w/2':y='H/2-3*h/4'[over4]; 
                    [5:v]scale={photo_scale},rotate='15*PI/180:ow=hypot(iw,ih):oh=ow:c=0x00000000'[v5];
                    [over4][v5]overlay=x='(3*W/4-w/2)':y='H/2-h/8'[over5];
                    [over5][6]overlay=y='(H-h)/2':x='W/2-w/4'" 
                            -t {last_remain_second} -r {fps} -crf 28 -preset ultrafast -b:v 2M -bufsize 2M -y {video_dir}/{save_dir}/end_7.mp4  -hide_banner -loglevel error""".replace(
            "\n", ""),
        shell=True)
    return result
