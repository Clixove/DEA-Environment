# Environment Protection DEA
 DEA Analysis of Environment Protection Investment

## 1. Background

The performance evaluation of environmental protection expenditure is a "multiple input, multiple output" problem: environmental protection agencies invest different amounts of funds in different projects, and environmental protection achievements are also determined by multiple indicators (different harmful gas emissions, the recycle ratios of different rubbish). In fact, there is no fixed metric (such as rate of return in business fields) to evaluate the performance of environmental protection.

This software is a web application software that evaluates and predicts the performance of environmental protection agencies. This software analyzes multiple input and output indicators, and uses the [DEA algorithm](https://en.wikipedia.org/wiki/Data_envelopment_analysis) to establish a performance indicator. This indicator aims to evaluate the performance of the decision-making unit (environmental protection agencies). This software also uses the BHT-ARIMA algorithm to implement short time series forecasting, to predict the performance of environmental protection agencies in the next year.

This software can help non-statistics users to quickly implement the DEA algorithm and the BHT-ARIMA algorithm proposed by the AAAI 2020 academic conference. It uses the contemporary popular models to calculate the performance of environmental protection expenditures.

## 2. Functions

Details in [documentation](./doc/基于数据包络分析的环境保护支出绩效评价软件-说明书.docx).

## 3. Acknowledgement

BHT-ARIMA: 
- Paper at https://arxiv.org/abs/2002.12135
- Code at https://github.com/huawei-noah/BHT-ARIMA

SourceHanSerifCN Font: https://github.com/wordshub/free-font#%E6%80%9D%E6%BA%90%E5%AE%8B%E4%BD%93

## 4. Software Design

Details in [documentation](./doc/基于数据包络分析的环境保护支出绩效评价软件-说明书.docx).

## 5. Installation

The current folder of command line is the software's project root.

### 5.1. Build token files

Create `token` folder at project root. There should be several files in this folder:
- In `token/django_secret_key`, there should be a string about 52 characters, being a secret key for communication between client and web server. 
- In `token/smtp.json`, there should be the config of web maintainer's email sender. The format is: 
```json
{
  "host": "example.com",
  "port": 465,
  "username": "registration@example.com",
  "password": "anypassword"
}
```
- In `token/paypal.json`, there should be paypal sandbox's clinet ID and secret. In formal release, please replace `SandboxEnvironment` in `__init__` function in `paypal/models.py > PaypalClient` class with `LiveEnvironment`, and use live's clinet ID and secret in `token/paypal.json`. The format is:
```json
{
  "client_id": "anypassword",
  "secret": "anypassword"
}
```

If you don't use a registration confirming service by email, `smtp.json` is not necessary. However, you should delete `add_register`, `send_confirm_email` functions and `RegisterSheet` class, and modify `add_user` function to link the result of `LoginForm` directly.

### 5.2.	Build Python environment

Install required Python packages:

```
pip install -r requirements.txt
```

It is a maximum required package. With the environment, all functions can be used, but not all functions are necessary.

Navigate to the project folder, and create the database and superuser:

```
python manage.py migrate
python manage.py createsuperuser
```

Follow the instructions in the command line. This user has the highest permission in this software.

### 5.3. Build static files

Replace `STATICFILES_DIRS = ['templates/static']` with `STATIC_ROOT = 'templates/static'` in `govt_env_protection_eval_dj/settings.py`.

Run the command: 
```
python manage.py collectstatic
```

Replace `STATIC_ROOT = 'templates/static'` with `STATICFILES_DIRS = ['templates/static']` in `govt_env_protection_eval_dj/settings.py`.

Replace `DEBUG = True` with `DEBUG = False` in `govt_env_protection_eval_dj/settings.py`.

### 5.4. Administrator's settings

Run the command: 
```
python manage.py 0.0.0.0:$port --insecure
```
The IP address can only be 127.0.0.1 (for local use only) or 0.0.0.0 (for web server), and `port` can be customized.

Visit [https://example.com:$port/admin](). Create at least one group. Add the groups, which users can freely add into, to "Register groups" table. These groups each must include the following permissions:
- My login: add, change, view Register
- Task manager: add, delete, change, view Task; add, delete, change, view AsyncErrorMessage;
  add, delete, change, view Column.
