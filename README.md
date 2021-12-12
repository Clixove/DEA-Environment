# Environment Protection DEA
 DEA Analysis of Environment Protection Investment

Chinese documentation: more details in 
[documentation](./doc/基于数据包络分析的环境保护支出绩效评价软件-说明书.docx)

## Introduction

The performance evaluation of environmental protection expenditure is a 
"multiple input, multiple output" problem: environmental protection agencies 
invest different amounts of funds in different projects, and environmental 
protection achievements are also determined by multiple indicators 
(different harmful gas emissions, the recycle ratios of different rubbish). 
In fact, there is no fixed metric (such as rate of return in business 
fields) to evaluate the performance of environmental protection.

This software is a web application software that evaluates and predicts the 
performance of environmental protection agencies. This software analyzes 
multiple input and output indicators, and uses the 
[DEA algorithm](https://en.wikipedia.org/wiki/Data_envelopment_analysis) to 
establish a performance indicator. This indicator aims to evaluate the 
performance of the decision-making unit (environmental protection agencies). 
This software also uses the BHT-ARIMA algorithm to implement short time 
series forecasting, to predict the performance of environmental protection 
agencies in the next year.

This software can help non-statistics users to quickly implement the DEA 
algorithm and the BHT-ARIMA algorithm proposed by the AAAI 2020 academic 
conference. It uses the contemporary popular models to calculate the 
performance of environmental protection expenditures.

## Acknowledgement

BHT-ARIMA: 
- Paper at https://arxiv.org/abs/2002.12135
- Code at https://github.com/huawei-noah/BHT-ARIMA

SourceHanSerifCN Font: https://github.com/wordshub/free-font#%E6%80%9D%E6%BA%90%E5%AE%8B%E4%BD%93

## Installation

The current folder of command line is the software's project root.

### 1. Token

Create a `token/` in project root, and include the following files in it.

(1) `django_secret_key`

There should be a string about 52 characters, being a secret key for 
communication between client and web server. The string can be generated in
[Djecrety](https://djecrety.ir/) website.

(2) `smtp.json`

If you don't use a registration confirming service by email, `smtp.json` is 
not necessary. At the same time, you should disable registry related links in
`govt_env_protection_eval_dj/urls.py`.

There should be the config of web maintainer's email sender in this file. 
The format is:

```json
{
  "host": "example.com",
  "port": 465,
  "username": "registration@example.com",
  "password": "anypassword"
}
```

### 2. Python environment

Install required Python packages:

```
pip install -r requirements.txt
```

It is a maximum required package. With the environment, all functions can be 
used, but not all functions are necessary.

Navigate to the project folder, and create the database and superuser:

```
python manage.py migrate
python manage.py createsuperuser
```

Follow the instructions in the command line. This user has the highest 
permission in this software.

### 3. Administrator's settings

Run the command: 

```
python manage.py 0.0.0.0:$port --insecure
```

The IP address can only be 127.0.0.1 (for local use only) or 0.0.0.0 (for web 
server), and `port` can be customized. After that, the website will be running
at `https://example.com:$port`.

(1) Registry permission

1. Visit `https://example.com:$port/admin`. 
2. Create at least one group instance, for example, named "Free plan" and
   users can freely register into.
3. Create a register group instance, and link to "Free plan".
4. Add proper permissions to "Free plan", at least including:
   "add, change, view Register", "add, delete, change, view Task", 
   "add, delete, change, view AsyncErrorMessage", and
   "add, delete, change, view Column".