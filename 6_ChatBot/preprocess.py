# -*- coding: utf-8 -*-
"""preprocess.py

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1D7rpyb-XYQevPtBuytpBY1Q9PgjLB1Hf

## Konlpy 설치
"""

# Commented out IPython magic to ensure Python compatibility.
# %%bash
# apt-get update
# apt-get install g++ openjdk-8-jdk python-dev python3-dev
# pip3 install JPype1
# pip3 install konlpy

# Commented out IPython magic to ensure Python compatibility.
# %env JAVA_HOME "/usr/lib/jvm/java-8-openjdk-amd64"

# Commented out IPython magic to ensure Python compatibility.
# %%bash
# bash <(curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh)
# pip3 install /tmp/mecab-python-0.996

import konlpy
from konlpy.tag import Kkma, Komoran, Hannanum, Okt
from konlpy.utils import pprint
from konlpy.tag import Mecab

mecab = Mecab()
sentence = "안녕하세요 저는 상휴입니다."
temp_X = mecab.morphs(sentence)
temp_X

"""## 데이터 전처리(preprocessing)

### 모듈 불러오기
"""

import os
import re
import json

import numpy as np
import pandas as pd
from tqdm import tqdm

from konlpy.tag import Okt

"""### 설정값 지정(특수문자 제거, 토큰 정의)"""

FILTERS = "([~.,!?\"':;)(])"
PAD = "<PAD>"
STD = "<SOS>"
END = "<END>"
UNK = "<UNK>"

PAD_INDEX = 0
STD_INDEX = 1
END_INDEX = 2
UNK_INDEX = 3

MARKER = [PAD, STD, END, UNK]
CHANGE_FILTER = re.compile(FILTERS)

MAX_SEQUENCE = 25

"""### 데이터 불러오기 및 질문, 답변 문장들을 리스트로 변환"""

def load_data(path):
    data_df = pd.read_csv(path, header=0)
    question, answer = list(data_df['Q']), list(data_df['A'])

    return question, answer

"""### 특수문자 제거 및 전체 문장에 대한 단어 리스트로 반환"""

def data_tokenizer(data):
    # 토크나이징 해서 담을 배열 생성
    words = []
    for sentence in data:
        # FILTERS = "([~.,!?\"':;)(])"
        # 위 필터와 같은 값들을 정규화 표현식을
        # 통해서 모두 "" 으로 변환 해주는 부분이다.
        sentence = re.sub(CHANGE_FILTER, "", sentence)
        for word in sentence.split():
            words.append(word)
    # 토그나이징과 정규표현식을 통해 만들어진
    # 값들을 넘겨 준다.
    return [word for word in words if word]

"""### 형태소 기준 텍스트 토크나이징 하여 각 문장을 형태소들의 리스트로 변환"""

def prepro_like_morphlized(data):
    morph_analyzer = Okt()
    result_data = list()
    for seq in tqdm(data):
        morphlized_seq = " ".join(morph_analyzer.morphs(seq.replace(' ', '')))
        result_data.append(morphlized_seq)

    return result_data

"""### 단어 사전 만들기"""

def load_vocabulary(path, vocab_path, tokenize_as_morph=False):
    # 사전 담을 리스트 준비.
    vocabulary_list = []
    # 파일의 존재 유무 확인
    if not os.path.exists(vocab_path):   
        if (os.path.exists(path)):
            # 데이터가 존재하면 불러옴
            data_df = pd.read_csv(path, encoding='utf-8')
            # 질문과 답에 대한 열
            question, answer = list(data_df['Q']), list(data_df['A'])
            if tokenize_as_morph:  # 형태소에 따른 토크나이징 처리
                question = prepro_like_morphlized(question)
                answer = prepro_like_morphlized(answer)
            data = []
            # .extend(전달값) : 전달값(iterable)을 하나하나 분해해서 리스트에 각 원소로 저장 (!! .append()와 구분!!) 
            data.extend(question)
            data.extend(answer)
            
            words = data_tokenizer(data)
            # 중복 단어 제거를 위한 set(집합) 이용.
            words = list(set(words))
            # MARKER를 사전에 추가 
            # 순서대로 넣기 위해서 인덱스 0에 추가한다.
            # PAD = "<PADDING>"
            # STD = "<START>"
            # END = "<END>"
            # UNK = "<UNKNWON>"
            words[:0] = MARKER

        # 리스트로된 단어 사전을 vocabulary_file이라는 곳에 저장, 각 단어는 개행문자(\n)를 오른쪽에 달고 하나씩 저장됨
        with open(vocab_path, 'w', encoding='utf-8') as vocabulary_file:
            for word in words:
                vocabulary_file.write(word + '\n')

    # 사전 파일이 존재하면 여기에서
    # 그 파일을 불러서 리스트에 추가 (이때 각 단어는 개행문자(\n)로 분리되어 저장되어있으므로, 각 개행문자를 .strip()으로 제거후 단어 사전 리스트로 저장)
    with open(vocab_path, 'r', encoding='utf-8') as vocabulary_file:
        for line in vocabulary_file:
            vocabulary_list.append(line.strip())

    # 리스트 내용을 키와 값이 있는
    # 사전 구조로 만든다.
    char2idx, idx2char = make_vocabulary(vocabulary_list)
    # 두가지 형태의 키와 값이 있는 형태를 리턴한다.
    # (예) 단어: 인덱스 , 인덱스: 단어)
    return char2idx, idx2char, len(char2idx)

'''
ls
'''

'''
a = ['one','two','three']
with open('colab Notebooks','w',encoding='utf-8') as vocab:
  for a1 in a:
    vocab.write(a1+'\n')
'''

'''
v1=[]
v2=[]
with open('colab Notebooks','r',encoding='utf-8') as vocab:
  for i in vocab:
    v1.append(i)
    v2.append(i.strip())
print(v1)
print(v2)
'''

def make_vocabulary(vocabulary_list):
    # 키가 단어이고 값이 인덱스인 사전
    char2idx = {char: idx for idx, char in enumerate(vocabulary_list)}
    # 키가 인덱스이고 값이 단어인 사전
    idx2char = {idx: char for idx, char in enumerate(vocabulary_list)}
    # 두개의 딕셔너리를 넘겨 준다.
    return char2idx, idx2char

def enc_processing(value, dictionary, tokenize_as_morph=False):
    # 인덱스 값.(누적된다.)
    sequences_input_index = []
    # 하나의 인코딩 되는 문장 길이.(누적된다.)
    sequences_length = []
    # 형태소 토크나이징 사용 유무
    if tokenize_as_morph:
        value = prepro_like_morphlized(value)

    # 한줄씩 불어온다.
    for sequence in value:
        # 특수문자 제거
        sequence = re.sub(CHANGE_FILTER, "", sequence)
        # 하나의 문장을 인코딩 할때 잠시 사용할 저장공간 : 매 문장마다 새로 만들어 사용할 것임
        sequence_index = []
        # 문장을 띄어쓰기 단위로 분리(단어가 됨)
        for word in sequence.split():
            # 잘려진 단어들이 단어 사전에 존재 하는지 보고
            # 그 값을 가져와 sequence_index에 추가
            if dictionary.get(word) is not None:
                sequence_index.extend([dictionary[word]])
            # 잘려진 단어가 딕셔너리에 존재 하지 않는
            # 경우 UNK(인덱스 : 3)를 넣어 준다.
            else:
                sequence_index.extend([dictionary[UNK]])
        # 문장 제한 길이보다 길어질 경우 뒤에 토큰을 자름
        if len(sequence_index) > MAX_SEQUENCE:
            sequence_index = sequence_index[:MAX_SEQUENCE]
        # 하나의 문장의 길이값 누적
        sequences_length.append(len(sequence_index))
        # max_sequence_length보다 문장 길이가
        # 작다면 빈 부분에 PAD(인덱스 0)를 넣어줌.
        sequence_index += (MAX_SEQUENCE - len(sequence_index)) * [dictionary[PAD]]
        # 인덱스화 되어 있는 값을
        # sequences_input_index에 넣어줌.
        sequences_input_index.append(sequence_index)
    # 인덱스화된 일반 배열을 넘파이 배열로 변경한다.
    # 이유는 텐서플로우 dataset에 넣어 주기 위한
    # 사전 작업.
    # 넘파이 배열에 인덱스화된 배열과 그 길이를 넘김.
    return np.asarray(sequences_input_index), sequences_length

def dec_output_processing(value, dictionary, tokenize_as_morph=False):
    # 인덱스화된 문장들의 리스트(누적된다)
    sequences_output_index = []
    # 하나의 디코딩에 입력 되는 문장의 길이.(누적된다)
    sequences_length = []
    # 형태소 토크나이징 사용 유무
    if tokenize_as_morph:
        value = prepro_like_morphlized(value)

    # 한줄씩 불러옴
    for sequence in value:
        # 특수문자 제거
        sequence = re.sub(CHANGE_FILTER, "", sequence)
        # 잠시 저장하는 공간
        sequence_index = []
        # 디코딩 입력의 처음에는 START가 와야 하므로 그 값을 넣어 주고 시작.
        # 문장에서 공백 단위별로 단어를 가져와서 사전의 값인 인덱스를 넣어 준다.
        sequence_index = [dictionary[STD]] + [dictionary[word] if word in dictionary else dictionary[UNK] for word in sequence.split()]
        # 문장 제한 길이보다 길어질 경우 뒤에 토큰을 자름.
        if len(sequence_index) > MAX_SEQUENCE:
            sequence_index = sequence_index[:MAX_SEQUENCE]
        # 하나의 문장에 길이를 넣어줌.
        sequences_length.append(len(sequence_index))
        # max_sequence_length보다 문장 길이가
        # 작다면 빈 부분에 PAD(인덱스 : 0)를 넣어줌.
        sequence_index += (MAX_SEQUENCE - len(sequence_index)) * [dictionary[PAD]]
        # 인덱스화 되어 있는 값을
        # sequences_output_index 넣어줌.
        sequences_output_index.append(sequence_index)
    # 인덱스화된 일반 배열을 넘파이 배열로 변경.
    # 이유는 텐서플로우 dataset에 넣어 주기 위한 사전 작업.
    # 넘파이 배열에 인덱스화된 배열과 그 길이를 넘겨줌.
    return np.asarray(sequences_output_index), sequences_length

def dec_target_processing(value, dictionary, tokenize_as_morph=False):
    # 인덱화된 문장들의 리스트.(누적된다)
    sequences_target_index = []
    # 형태소 토크나이징 사용 유무
    if tokenize_as_morph:
        value = prepro_like_morphlized(value)
    # 한줄씩 불러옴.
    for sequence in value:
        # 특수문자 제거
        sequence = re.sub(CHANGE_FILTER, "", sequence)
        # 문장 인덱스화
        # 디코딩 출력의 마지막에 END를 넣어 준다.
        sequence_index = [dictionary[word] if word in dictionary else dictionary[UNK] for word in sequence.split()]
        # 문장 제한 길이보다 길어질 경우 뒤에 토큰을 자름.
        # 그리고 END 토큰을 넣어 준다
        if len(sequence_index) >= MAX_SEQUENCE:
            sequence_index = sequence_index[:MAX_SEQUENCE - 1] + [dictionary[END]]
        else:
            sequence_index += [dictionary[END]]
        # max_sequence_length보다 문장 길이가
        # 작다면 빈 부분에 PAD(0)를 넣어준다.
        sequence_index += (MAX_SEQUENCE - len(sequence_index)) * [dictionary[PAD]]
        # 인덱스화 되어 있는 값을
        # sequences_target_index에 넣어 준다.
        sequences_target_index.append(sequence_index)
    # 인덱스화된 일반 배열을 넘파이 배열로 변경.
    # 이유는 텐서플로우 dataset에 넣어 주기 위한 사전 작업.
    # 넘파이 배열에 인덱스화된 배열과 그 길이를 넘겨줌.
    return np.asarray(sequences_target_index)