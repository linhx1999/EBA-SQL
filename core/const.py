MAX_ROUND = 3 
# DESC_LEN_LIMIT = 200  # max length of description of each column (counted by char)
# MAX_OUTPUT_LEN = 1000  # max length of output (counted by tokens)
# RATIO = 0.8  # soft upper bound of max

ENGINE_GPT4 = 'gpt-4'
ENGINE_GPT4_32K = 'gpt-4-32k'

EBA_DRIVEN_SELECTOR_NAME = 'EBA_Driven_Selector'
EBA_DRIVEN_DECOMPOSER_NAME = 'EBA_Driven_Decomposer'
ERROR_DRIVEN_REFINER_NAME = 'Error_Driven_Refiner'
SYSTEM_NAME = 'System'

summarizer_template = """
[instruction]
Given the database schema, you need to summarise the data stored in each table in one sentence, based on the name of the table and the columns in the table.

[Requirements]
- Your output should be in json format

Here is an example:
==========

【DB_ID】 banking_system
【Schema】
# Table: account
[
  (account_id <INTEGER>, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
  (district_id <INTEGER>, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (frequency <TEXT>, frequency of the acount. Value examples: ['POPLATEK MESICNE', 'POPLATEK TYDNE', 'POPLATEK PO OBRATU'].),
  (date <DATE>, the creation date of the account. Value examples: ['1997-12-29', '1997-12-28'].)
]
# Table: client
[
  (client_id <INTEGER>, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
  (gender <TEXT>, gender. Value examples: ['M', 'F']. And F：female . M：male ),
  (birth_date <DATE>, birth date. Value examples: ['1987-09-27', '1986-08-13'].),
  (district_id <INTEGER>, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (first_name <TEXT>, first_name.),
  (last_name <TEXT>, last_name.)
]
# Table: loan
[
  (loan_id <INTEGER>, the id number identifying the loan data. Value examples: [4959, 4960, 4961].),
  (account_id <INTEGER>, the id number identifying the account. Value examples: [10, 80, 55, 43].),
  (date <DATE>, the date when the loan is approved. Value examples: ['1998-07-12', '1998-04-19'].),
  (amount <INTEGER>, the id number identifying the loan data. Value examples: [1567, 7877, 9988].),
  (duration <INTEGER>, the id number identifying the loan data. Value examples: [60, 48, 24, 12, 36].),
  (payments <INTEGER>, the id number identifying the loan data. Value examples: [3456, 8972, 9845].),
  (status <TEXT>, the id number identifying the loan data. Value examples: ['C', 'A', 'D', 'B'].)
]
# Table: district
[
  (district_id <INTEGER>, location of branch. Value examples: [77, 76].),
  (A2 <REAL>, area in square kilometers. Value examples: [50.5, 48.9].),
  (A4 <INTEGER>, number of inhabitants. Value examples: [95907, 95616].),
  (A5 <INTEGER>, number of households. Value examples: [35678, 34892].),
  (A6 <REAL>, literacy rate. Value examples: [95.6, 92.3, 89.7].),
  (A7 <INTEGER>, number of entrepreneurs. Value examples: [1234, 1456].),
  (A8 <INTEGERt>, number of cities. Value examples: [5, 4].),
  (A9 <INTEGER>, number of schools. Value examples: [15, 12, 10].),
  (A10 <INTEGER>, number of hospitals. Value examples: [8, 6, 4].),
  (A11 <REAL>, average salary. Value examples: [12541.5, 11277].),
  (A12 <REAL>, poverty rate. Value examples: [12.4, 9.8].),
  (A13 <REAL>, unemployment rate. Value examples: [8.2, 7.9].),
  (A15 <INTEGER>, number of crimes. Value examples: [256, 189].)
]

【Summary】
```json
{{
    "account":"Specific information for each account",
    "client":"Basic information about each client",
    "loan":"Detailed records of each loan",
    "district":"Various data recorded in each district",

}}
```
==========

Here is a new case:
【DB_ID】 {db_id}
【Schema】
{desc_str}

【Summary】
"""

selector_difficult = """
As an experienced and professional database administrator, your task is to analyze a user question and a database schema to provide relevant information. The database schema consists of table descriptions, each containing multiple column descriptions. Your goal is to extract the entities from question and identify the relevant tables and columns based on these entities and the evidence provided.

[Instruction]:
1. Extract the mentioned entities from the user question. Make sure all of the entities are extracted. 
2. For each entity, keep at least 3 related columns.
3. Your output should include entity extraction, analysis and related database schema.
4. The related database schema should be in JSON format.
5. Each column's information in provided 【Schema】 is in this format: (column, description. Value examples<optional>)

[Requirements]:
1. Sort the related columns in each list corresponding to each entity in descending order of relevance.
2. The chosen columns should be in this format: <table.column>.
3. Make sure each chosen list is not empty. The value [] will be punished. 
4.【Matched values】 may contain redundant or useless information in addition to the correct matching values, so you need to select the useful information in conjunction with the specific column names and descriptions.
5. An entity may not have a corresponding evidence, which requires you to find the relevant columns yourself through your understanding of the database schema.

Here is a typical example:

==========
【DB_ID】 banking_system
【Schema】
# Table: account
[
  (account_id <INTEGER>, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
  (district_id <INTEGER>, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (frequency <TEXT>, frequency of the acount. Value examples: ['POPLATEK MESICNE', 'POPLATEK TYDNE', 'POPLATEK PO OBRATU'].),
  (date <DATE>, the creation date of the account. Value examples: ['1997-12-29', '1997-12-28'].)
]
# Table: client
[
  (client_id <INTEGER>, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
  (gender <TEXT>, gender. Value examples: ['M', 'F']. And F：female . M：male ),
  (birth_date <DATE>, birth date. Value examples: ['1987-09-27', '1986-08-13'].),
  (district_id <INTEGER>, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (first_name <TEXT>, first_name.),
  (last_name <TEXT>, last_name.)
]
# Table: loan
[
  (loan_id <INTEGER>, the id number identifying the loan data. Value examples: [4959, 4960, 4961].),
  (account_id <INTEGER>, the id number identifying the account. Value examples: [10, 80, 55, 43].),
  (date <DATE>, the date when the loan is approved. Value examples: ['1998-07-12', '1998-04-19'].),
  (amount <INTEGER>, the id number identifying the loan data. Value examples: [1567, 7877, 9988].),
  (duration <INTEGER>, the id number identifying the loan data. Value examples: [60, 48, 24, 12, 36].),
  (payments <INTEGER>, the id number identifying the loan data. Value examples: [3456, 8972, 9845].),
  (status <TEXT>, the id number identifying the loan data. Value examples: ['C', 'A', 'D', 'B'].)
]
# Table: district
[
  (district_id <INTEGER>, location of branch. Value examples: [77, 76].),
  (A2 <REAL>, area in square kilometers. Value examples: [50.5, 48.9].),
  (A4 <INTEGER>, number of inhabitants. Value examples: [95907, 95616].),
  (A5 <INTEGER>, number of households. Value examples: [35678, 34892].),
  (A6 <REAL>, literacy rate. Value examples: [95.6, 92.3, 89.7].),
  (A7 <INTEGER>, number of entrepreneurs. Value examples: [1234, 1456].),
  (A8 <INTEGERt>, number of cities. Value examples: [5, 4].),
  (A9 <INTEGER>, number of schools. Value examples: [15, 12, 10].),
  (A10 <INTEGER>, number of hospitals. Value examples: [8, 6, 4].),
  (A11 <REAL>, average salary. Value examples: [12541.5, 11277].),
  (A12 <REAL>, poverty rate. Value examples: [12.4, 9.8].),
  (A13 <REAL>, unemployment rate. Value examples: [8.2, 7.9].),
  (A15 <INTEGER>, number of crimes. Value examples: [256, 189].)
]
【Primary keys】
account.`account_id` | client.`client_id` | loan.`loan_id` | district.`district_id`
【Foreign keys】
client.`district_id` = district.`district_id`
【Question】
What is the gender of the youngest client who opened account in the lowest average salary branch and when did this client open the account? Please list their full name.
【Evidence】
Later birthdate refers to younger age; A11 refers to average salary; Full name refers to first_name, last_name
【Matched values】
Since some of the specific values in Question and evidence match the data in the database, here are some matches retrieved from the database that may help you in selecting columns (You need to ignore matches that are not relevant to the question):
No matched values.
【Answer】
The entities extracted from the 【Question】 are: 
1. gender; 
2. youngest client; 
3. account; 
4. lowest average salary branch; 
5. when did this client open the account; 
6. full name

Extract the related evidence in 【Evidence】 for entities if 【Evidence】 is not None: 
1. gender --no related evidence **the columns about gender are related**
2. youngest client  --Later birthdate refers to younger age; **the columns about birth date of client and the id of client are related**
3. account --no related evidence **the columns about account or account ids are related**
4. lowest average salary branch  --A11 refers to average salary **the columns about average salary and branch are related**
5. when did this client open the account --no related evidence **the columns about time or date of the account are related**
6. full name  --Full name refers to first_name, last_name **the columns about first_name, last_name of the client are related**

Therefore, we can select the related database schema based on these entities with 【Evidence】:
```json
{{
  "gender": ["client.gender","client.client_id","loan.status"],
  "youngest client": ["client.birth_date","client.client_id","account.date","loan.date"],
  "account": ["account.account_id","loan.account_id","account.date"],
  "lowest average salary branch": ["district.A11","district.district_id","district.A13"],
  "when did this client open the account": ["account.date","loan.date","client.birth_date"],
  "full name": ["client.first_name","client.last_name","client.client_id"]
}}
```
Question Solved.

==========

Here is a new example, please start answering:

【DB_ID】 {db_id}
【Schema】
{desc_str}
【Primary keys】
{pk_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}
【Matched values】
Since some of the specific values in Question and evidence match the data in the database, here are some matches retrieved from the database that may help you in selecting columns (You need to ignore matches that are not relevant to the question):
{matched_list}
【Answer】
"""

subq_pattern = r"Sub question\s*\d+\s*:"

decompose_template_bird = """
Given a 【Database schema】 description, a knowledge 【Evidence】 and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then decompose the question into subquestions for text-to-SQL generation.
When decomposing the question into subquestions, we should always consider Instructions:
【Instructions】
1. Extract the mentioned entities from the user question. Make sure all of the entities are extracted. 
2. Your output should include entity extraction, entity based intent analysis and entity based sub-question decomposition.
3. Generate corresponding SQL based on decomposed sub questions.
4. The final sub question should be 【Question】.

When generating SQL, we should always consider constraints:
【Constraints】
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- If include more than one table, use `JOIN <table>`
- If use `JOIN <table>`, the connected columns should be in the 【Foreign keys】
- If evidence gives a formula for calculating a value, try to use that formula
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected


==========

【Database schema】
# Table: frpm
[
  (CDSCode, CDSCode. Value examples: ['01100170109835', '01100170112607'].),
  (Charter School (Y/N), Charter School (Y/N). Value examples: [1, 0, None]. And 0: N;. 1: Y),
  (Enrollment (Ages 5-17), Enrollment (Ages 5-17). Value examples: [5271.0, 4734.0].),
  (Free Meal Count (Ages 5-17), Free Meal Count (Ages 5-17). Value examples: [3864.0, 2637.0]. And eligible free rate = Free Meal Count / Enrollment)
]
# Table: satscores
[
  (cds, California Department Schools. Value examples: ['10101080000000', '10101080109991'].),
  (sname, school name. Value examples: ['None', 'Middle College High', 'John F. Kennedy High', 'Independence High', 'Foothill High'].),
  (NumTstTakr, Number of Test Takers in this school. Value examples: [24305, 4942, 1, 0, 280]. And number of test takers in each school),
  (AvgScrMath, average scores in Math. Value examples: [699, 698, 289, None, 492]. And average scores in Math),
  (NumGE1500, Number of Test Takers Whose Total SAT Scores Are Greater or Equal to 1500. Value examples: [5837, 2125, 0, None, 191]. And Number of Test Takers Whose Total SAT Scores Are Greater or Equal to 1500. . commonsense evidence:. . Excellence Rate = NumGE1500 / NumTstTakr)
]
【Foreign keys】
frpm.`CDSCode` = satscores.`cds`
【Question】
List school names of charter schools with an SAT excellence rate over the average.
【Evidence】
Charter schools refers to `Charter School (Y/N)` = 1 in the table frpm; Excellence rate = NumGE1500 / NumTstTakr


Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Analysis:
The entities extracted: school names; charter schools; SAT excellence rate;
Entity based intent analysis: The question requires listing school names of charter schools where the SAT excellence rate exceeds the average SAT excellence rate of all charter schools.
Entity based sub-question decomposition: 
Sub question 1: Get the average value of SAT excellence rate of charter schools. (This calculates the average value of the ratio NumGE1500 / NumTstTakr for all rows where Charter School (Y/N) = 1.)
Sub question 2: List school names of charter schools with an SAT excellence rate over the average. (The final question.)

Sub question 1: Get the average value of SAT excellence rate of charter schools.
SQL
```sql
SELECT AVG(CAST(T2.`NumGE1500` AS REAL) / T2.`NumTstTakr`)
    FROM frpm AS T1
    INNER JOIN satscores AS T2
    ON T1.`CDSCode` = T2.`cds`
    WHERE T1.`Charter School (Y/N)` = 1
```

Sub question 2: List school names of charter schools with an SAT excellence rate over the average.
SQL
```sql
SELECT T2.`sname`
  FROM frpm AS T1
  INNER JOIN satscores AS T2
  ON T1.`CDSCode` = T2.`cds`
  WHERE T2.`sname` IS NOT NULL
  AND T1.`Charter School (Y/N)` = 1
  AND CAST(T2.`NumGE1500` AS REAL) / T2.`NumTstTakr` > (
    SELECT AVG(CAST(T4.`NumGE1500` AS REAL) / T4.`NumTstTakr`)
    FROM frpm AS T3
    INNER JOIN satscores AS T4
    ON T3.`CDSCode` = T4.`cds`
    WHERE T3.`Charter School (Y/N)` = 1
  )
```

Question Solved.

==========

【Database schema】
# Table: account
[
  (account_id, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (frequency, frequency of the acount. Value examples: ['POPLATEK MESICNE', 'POPLATEK TYDNE', 'POPLATEK PO OBRATU'].),
  (date, the creation date of the account. Value examples: ['1997-12-29', '1997-12-28'].)
]
# Table: client
[
  (client_id, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
  (gender, gender. Value examples: ['M', 'F']. And F：female . M：male ),
  (birth_date, birth date. Value examples: ['1987-09-27', '1986-08-13'].),
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].)
]
# Table: district
[
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (A4, number of inhabitants . Value examples: ['95907', '95616', '94812'].),
  (A11, average salary. Value examples: [12541, 11277, 8114].)
]
【Foreign keys】
account.`district_id` = district.`district_id`
client.`district_id` = district.`district_id`
【Question】
What is the gender of the youngest client who opened account in the lowest average salary branch?
【Evidence】
Later birthdate refers to younger age; A11 refers to average salary

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Analysis:
The entities extracted: gender; youngest client; opened account; lowest average salary branch;
Entity based intent analysis: The question asks to find the gender of the youngest client (based on birthdate) who opened an account in the branch with the lowest average salary.
Entity based sub-question decomposition: 
Sub question 1: What is the district_id of the branch with the lowest average salary? (This identifies the branch (via district_id) with the smallest value in the A11 column.)
Sub question 2: What is the youngest client who opened account in the lowest average salary branch? (This filters clients to those who opened accounts in the branch with the district_id found in Sub-question 1, and identifies the client with the latest birthdate (younger age).)
Sub question 3: What is the gender of the youngest client who opened account in the lowest average salary branch? (The final question.)

Sub question 1: What is the district_id of the branch with the lowest average salary?
SQL
```sql
SELECT `district_id`
  FROM district
  ORDER BY `A11` ASC
  LIMIT 1
```

Sub question 2: What is the youngest client who opened account in the lowest average salary branch?
SQL
```sql
SELECT T1.`client_id`
  FROM client AS T1
  INNER JOIN district AS T2
  ON T1.`district_id` = T2.`district_id`
  ORDER BY T2.`A11` ASC, T1.`birth_date` DESC 
  LIMIT 1
```

Sub question 3: What is the gender of the youngest client who opened account in the lowest average salary branch?
SQL
```sql
SELECT T1.`gender`
  FROM client AS T1
  INNER JOIN district AS T2
  ON T1.`district_id` = T2.`district_id`
  ORDER BY T2.`A11` ASC, T1.`birth_date` DESC 
  LIMIT 1 
```
Question Solved.

==========

【Database schema】
{desc_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
"""

decompose_template_bird_difficult = """
Given a 【Database schema】 description, a knowledge 【Evidence】 and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then decompose the question into subquestions for text-to-SQL generation.
When decomposing the question into subquestions, we should always consider Instructions:
【Instructions】
1. Extract the mentioned entities from the user question. Make sure all of the entities are extracted. 
2. Your output should include entity extraction, entity based intent analysis and entity based sub-question decomposition.
3. Generate corresponding SQL based on decomposed sub questions.
4. The final sub question should be 【Question】.

When generating SQL, we should always consider constraints:
【Constraints】
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- If include more than one table, use `JOIN <table>`
- If use `JOIN <table>`, the connected columns should be in the 【Foreign keys】
- If evidence gives a formula for calculating a value, try to use that formula
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected

==========

【Database schema】
# country: [origin (INTEGER), country(TEXT)]
# price: [ID (INTEGER), price (REAL)]
# data: [ID (INTEGER), mpg (REAL), cylinders (INTEGER), displacement (TEXT), horsepower (REAL), weight (REAL), acceleration (REAL), model (TEXT), car_name (TEXT)]
# production: [ID (INTEGER), model_year (INTEGER), country (INTEGER)]
【Primary keys】
country.`origin` | price.`ID` | data.`ID` | production.`ID`
【Foreign keys】
data.`ID` = price.`ID`
production.`ID` = price.`ID`
production.`ID` = data.`ID`
production.`country` = country.`origin`
【Detailed descriptions of tables and columns】
country.`origin`: The column 'origin' in Table <country> has column descriptions of "the unique identifier for the origin country". Value examples: [1, 2, 3].
country.`country`: The column 'country' in Table <country> has column descriptions of "the origin country of the car". Value examples: ['USA', 'Japan', 'Europe'].
data.`horsepower`:  The column 'horsepower' in Table <data> has column descriptions of "horse power associated with the car".
data.`acceleration`:  The column 'acceleration' in Table <data> has column descriptions of "acceleration of the car in miles per squared hour".
production.`country`: The column 'country' in Table <production> has column descriptions of "country id to which the car belongs".  Value examples: [1, 2, 3].
【Evidence】
the fastest refers to max(horsepower); name of the car refers to car_name
【Question】
What is the price of the fastest car made by Japan?
【Matched values】
Since some of the specific values in Question and evidence match the data in the database, here are some matches retrieved from the database that may help you to generate SQL (Matched values may contain useless information and you should ignore matches that are not relevant to the question):
country.`country` = 'Japan'

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Analysis:
The entities extracted: price; car; Japan;
Entity based intent analysis: The intent of the question is to find out the price of the fastest car manufactured in Japan. The question requires understanding the term "fastest" (which refers to the car with the maximum horsepower) and filtering the result based on the manufacturer country, Japan.
Entity based sub-question decomposition: 
Sub question 1: What is the price of the fastest car? (This extracts the price of the fastest car without considering the manufacturing location.)
Sub question 2: What is the fastest car made by Japan? (This identifies the fastest car (by maximum horsepower) manufactured in Japan.)
Sub question 3: What is the price of the fastest car made by Japan? (The final question.)

Sub question 1: What is the price of the fastest car?
SQL
```sql
SELECT T1.`price` 
  FROM price AS T1 
  INNER JOIN data AS T2 
  ON T2.`ID` = T1.`ID` 
  ORDER BY T2.`horsepower` 
  DESC LIMIT 1
```


Sub question 2: What is the fastest car made by Japan?
SQL
```sql
SELECT T1.`car_name` 
  FROM data AS T1 
  INNER JOIN production AS T2 
  ON T1.`ID` = T2.`ID` 
  INNER JOIN country AS T3 
  ON T3.`origin` = T2.`country` 
  WHERE T3.`country` = 'Japan' 
  ORDER BY T1.`horsepower` DESC LIMIT 1
```

Sub question 3: What is the price of the fastest car made by Japan?
SQL
```sql
SELECT T1.`price` 
  FROM price AS T1 
  INNER JOIN data AS T2
  on T2.`ID` = T1.`ID`
  INNER JOIN production AS T3 
  ON T3.`ID` = T2.`ID` 
  INNER JOIN country AS T4 
  ON T4.`origin` = T3.`country` 
  WHERE T4.`country` = 'Japan' 
  ORDER BY T2.`horsepower` DESC LIMIT 1
```
Question Solved.

==========

【Database schema】
# institution_details: [unitid (INTEGER), chronname (TEXT), city (TEXT), state (TEXT), site (TEXT), student_count(TEXT)]
# institution_grads: [unitid (INTEGER), gender (TEXT), race (TEXT), cohhort (TEXT)]
【Primary keys】
institution_details.`unitid` | institution_grads.`unitid`
【Foreign keys】
institution_grads.`unitid` = institution_details.`unitid`
【Detailed descriptions of tables and columns】
institution_details.`unitid`: The column 'unitid' in Table <institution_details> has column descriptions of "Education Unit ID number". 
institution_details.`chronname`: The column 'chronname' in Table <institution_details> has column descriptions of "Institution name". 
institution_details.`student_count`: The column 'student_count' in Table <institution_details> has column descriptions of "Total number of undergraduates in 2010". 
【Evidence】
number of students greater than the 90% of average = MULTIPLY(AVG(student_count), 90%) < student_count
【Question】
List the race of institutions in Alabama with number of students greater than the 90% of average number of students of all institutions?
【Matched values】
Since some of the specific values in Question and evidence match the data in the database, here are some matches retrieved from the database that may help you to generate SQL (Matched values may contain useless information and you should ignore matches that are not relevant to the question):
No matched values.

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Analysis:
The entities extracted: race; institutions in Alabama; number of students;
Entity based intent analysis: The question intends to retrieve the race of institutions in Alabama where the number of students is greater than 90% of the average number of students across all institutions.
Entity based sub-question decomposition: 
Sub question 1: List the race of institution in Alabama. (This determines the race of institution in Alabama.)
Sub question 2: List the race of institutions in Alabama with number of students greater than the 90% of average number of students of all institutions? (The final question.)

Sub question 1: List the race of institution in Alabama.
SQL
```sql
SELECT DISTINCT T1.`race` 
  FROM institution_grads AS T1 
  INNER JOIN institution_details AS T2 
  ON T1.`unitid` = T2.`unitid` 
  WHERE T2.`state` = 'Alabama'
```

Sub question 2: List the race of institutions in Alabama with number of students greater than the 90% of average number of students of all institutions?
SQL
```sql
SELECT DISTINCT T1.`race` 
  FROM institution_grads AS T1 
  INNER JOIN institution_details AS T2 
  ON T1.`unitid` = T2.`unitid` 
  WHERE T2.`student_count` > ( 
    SELECT AVG(`student_count`) * 0.9 FROM institution_details 
  ) 
  AND T2.`state` = 'Alabama'
```
Question Solved.

==========

【Database schema】
{desc_str}
【Primary keys】
{pk_str}
【Foreign keys】
{fk_str}
【Detailed descriptions of tables and columns】
{detailed_str}
【Evidence】
{evidence}
【Question】
{query}
【Matched values】
Since some of the specific values in Question and evidence match the data in the database, here are some matches retrieved from the database that may help you to generate SQL (Matched values may contain useless information and you should ignore matches that are not relevant to the question):
{matched_list}

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
"""

decompose_template_spider = """
Given a 【Database schema】 description, and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then decompose the question into subquestions for text-to-SQL generation.
When decomposing the question into subquestions, we should always consider Instructions:
【Instructions】
1. Extract the mentioned entities from the user question. Make sure all of the entities are extracted. 
2. Your output should include entity extraction, entity based intent analysis and entity based sub-question decomposition.
3. Generate corresponding SQL based on decomposed sub questions.
4. The final sub question should be 【Question】.

When generating SQL, we should always consider constraints:
【Constraints】
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- If include more than one table, use `JOIN <table>`
- If use `JOIN <table>`, the connected columns should be in the 【Foreign keys】
- If evidence gives a formula for calculating a value, try to use that formula
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected

==========

【Database schema】
# Table: stadium
[
  (Stadium_ID, stadium id. Value examples: [1, 2, 3, 4, 5, 6].),
  (Location, location. Value examples: ['Stirling Albion', 'Raith Rovers', "Queen's Park", 'Peterhead', 'East Fife', 'Brechin City'].),
  (Name, name. Value examples: ["Stark's Park", 'Somerset Park', 'Recreation Park', 'Hampden Park', 'Glebe Park', 'Gayfield Park'].),
  (Capacity, capacity. Value examples: [52500, 11998, 10104, 4125, 4000, 3960].),
  (Highest, highest. Value examples: [4812, 2363, 1980, 1763, 1125, 1057].),
  (Lowest, lowest. Value examples: [1294, 1057, 533, 466, 411, 404].),
  (Average, average. Value examples: [2106, 1477, 864, 730, 642, 638].)
]
# Table: concert
[
  (concert_ID, concert id. Value examples: [1, 2, 3, 4, 5, 6].),
  (concert_Name, concert name. Value examples: ['Week 1', 'Week 2', 'Super bootcamp', 'Home Visits', 'Auditions'].),
  (Theme, theme. Value examples: ['Wide Awake', 'Party All Night', 'Happy Tonight', 'Free choice 2', 'Free choice', 'Bleeding Love'].),
  (Stadium_ID, stadium id. Value examples: ['2', '9', '7', '10', '1'].),
  (Year, year. Value examples: ['2015', '2014'].)
]
【Foreign keys】
concert.`Stadium_ID` = stadium.`Stadium_ID`
【Question】
Show the stadium name and the number of concerts in each stadium.

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Analysis:
The entities extracted: stadium name; number of concerts;
Entity based intent analysis: The goal is to list the stadium names and the number of concerts held in each stadium.
Entity based sub-question decomposition: 
Sub question 1: Show the stadium name for each stadium. (This retrieves the names of all stadiums.)
Sub question 2: Show the number of concerts in each stadium. (This counts the number of concerts grouped by each stadium.)
Sub question 3: Show the stadium name and the number of concerts in each stadium. (The final question.)

Sub question 1: Show the stadium name for each stadium.
SQL
```sql
SELECT `Name` FROM stadium
```

Sub question 2: Show the number of concerts in each stadium.
SQL
```sql
SELECT COUNT(*) FROM stadium AS T1 JOIN concert AS T2 ON T1.`Stadium_ID` = T2.`Stadium_ID` GROUP BY T1.`Stadium_ID`
```

Sub question 3: Show the stadium name and the number of concerts in each stadium.
SQL
```sql
SELECT T1.`Name`, COUNT(*) FROM stadium AS T1 JOIN concert AS T2 ON T1.`Stadium_ID` = T2.`Stadium_ID` GROUP BY T1.`Stadium_ID`
```
Question Solved.

==========

【Database schema】
# Table: singer
[
  (Singer_ID, singer id. Value examples: [1, 2].),
  (Name, name. Value examples: ['Tribal King', 'Timbaland'].),
  (Country, country. Value examples: ['France', 'United States', 'Netherlands'].),
  (Song_Name, song name. Value examples: ['You', 'Sun', 'Love', 'Hey Oh'].),
  (Song_release_year, song release year. Value examples: ['2016', '2014'].),
  (Age, age. Value examples: [52, 43].)
]
# Table: concert
[
  (concert_ID, concert id. Value examples: [1, 2].),
  (concert_Name, concert name. Value examples: ['Super bootcamp', 'Home Visits', 'Auditions'].),
  (Theme, theme. Value examples: ['Wide Awake', 'Party All Night'].),
  (Stadium_ID, stadium id. Value examples: ['2', '9'].),
  (Year, year. Value examples: ['2015', '2014'].)
]
# Table: singer_in_concert
[
  (concert_ID, concert id. Value examples: [1, 2].),
  (Singer_ID, singer id. Value examples: ['3', '6'].)
]
【Foreign keys】
singer_in_concert.`Singer_ID` = singer.`Singer_ID`
singer_in_concert.`concert_ID` = concert.`concert_ID`
【Question】
Show the name and the release year of the song by the youngest singer.

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Analysis:
The entities extracted: name of the song; release year of the song; youngest singer;
Entity based intent analysis: The question requires displaying the name and release year of a song performed by the youngest singer. The key is identifying the youngest singer (based on age or birthdate) and retrieving the desired details about their song.
Entity based sub-question decomposition: 
Sub question 1: Show the name of the song by the youngest singer. (This sub-question focuses on retrieving the song name associated with the youngest singer.)
Sub question 2: Show the release year of the song by the youngest singer. (This sub-question retrieves the release year of the song performed by the youngest singer.)
Sub question 3: Show the name and the release year of the song by the youngest singer. (The final question.)

Sub question 1: Show the name of the song by the youngest singer.
SQL
```sql
SELECT `Song_Name` FROM singer WHERE Age = (SELECT MIN(Age) FROM singer)
```

Sub question 2: Show the release year of the song by the youngest singer.
SQL
```sql
SELECT `Song_release_year` FROM singer WHERE Age = (SELECT MIN(Age) FROM singer)
```

Sub question 3: Show the name and the release year of the song by the youngest singer.
SQL
```sql
SELECT `Song_Name`, `Song_release_year` FROM singer WHERE Age = (SELECT MIN(Age) FROM singer)
```
Question Solved.

==========

【Database schema】
{desc_str}
【Foreign keys】
{fk_str}
【Primary keys】
{pk_str}
【Detailed descriptions of tables and columns】
{detailed_str}
【Question】
{query}


Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
"""


oneshot_template_1 = """
Given a 【Database schema】 description, a knowledge 【Evidence】 and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then decompose the question into subquestions for text-to-SQL generation.
When generating SQL, we should always consider constraints:
【Constraints】
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

==========

【Database schema】
# Table: frpm
[
  (CDSCode, CDSCode. Value examples: ['01100170109835', '01100170112607'].),
  (Charter School (Y/N), Charter School (Y/N). Value examples: [1, 0, None]. And 0: N;. 1: Y),
  (Enrollment (Ages 5-17), Enrollment (Ages 5-17). Value examples: [5271.0, 4734.0, 4718.0].),
  (Free Meal Count (Ages 5-17), Free Meal Count (Ages 5-17). Value examples: [3864.0, 2637.0, 2573.0]. And eligible free rate = Free Meal Count / Enrollment)
]
# Table: satscores
[
  (cds, California Department Schools. Value examples: ['10101080000000', '10101080109991'].),
  (sname, school name. Value examples: ['None', 'Middle College High', 'John F. Kennedy High', 'Independence High', 'Foothill High'].),
  (NumTstTakr, Number of Test Takers in this school. Value examples: [24305, 4942, 1, 0, 280]. And number of test takers in each school),
  (AvgScrMath, average scores in Math. Value examples: [699, 698, 289, None, 492]. And average scores in Math),
  (NumGE1500, Number of Test Takers Whose Total SAT Scores Are Greater or Equal to 1500. Value examples: [5837, 2125, 0, None, 191]. And Number of Test Takers Whose Total SAT Scores Are Greater or Equal to 1500. And commonsense evidence: Excellence Rate = NumGE1500 / NumTstTakr)
]
【Foreign keys】
frpm.`CDSCode` = satscores.`cds`
【Question】
List school names of charter schools with an SAT excellence rate over the average.
【Evidence】
Charter schools refers to `Charter School (Y/N)` = 1 in the table frpm; Excellence rate = NumGE1500 / NumTstTakr


Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Sub question 1: Get the average value of SAT excellence rate of charter schools.
SQL
```sql
SELECT AVG(CAST(T2.`NumGE1500` AS REAL) / T2.`NumTstTakr`)
    FROM frpm AS T1
    INNER JOIN satscores AS T2
    ON T1.`CDSCode` = T2.`cds`
    WHERE T1.`Charter School (Y/N)` = 1
```

Sub question 2: List out school names of charter schools with an SAT excellence rate over the average.
SQL
```sql
SELECT T2.`sname`
  FROM frpm AS T1
  INNER JOIN satscores AS T2
  ON T1.`CDSCode` = T2.`cds`
  WHERE T2.`sname` IS NOT NULL
  AND T1.`Charter School (Y/N)` = 1
  AND CAST(T2.`NumGE1500` AS REAL) / T2.`NumTstTakr` > (
    SELECT AVG(CAST(T4.`NumGE1500` AS REAL) / T4.`NumTstTakr`)
    FROM frpm AS T3
    INNER JOIN satscores AS T4
    ON T3.`CDSCode` = T4.`cds`
    WHERE T3.`Charter School (Y/N)` = 1
  )
```

Question Solved.

==========

【Database schema】
{desc_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
"""


oneshot_template_2 = """
Given a 【Database schema】 description, a knowledge 【Evidence】 and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then decompose the question into subquestions for text-to-SQL generation.
When generating SQL, we should always consider constraints:
【Constraints】
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

==========

【Database schema】
# Table: account
[
  (account_id, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (frequency, frequency of the acount. Value examples: ['POPLATEK MESICNE', 'POPLATEK TYDNE', 'POPLATEK PO OBRATU'].),
  (date, the creation date of the account. Value examples: ['1997-12-29', '1997-12-28'].)
]
# Table: client
[
  (client_id, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
  (gender, gender. Value examples: ['M', 'F']. And F：female . M：male ),
  (birth_date, birth date. Value examples: ['1987-09-27', '1986-08-13'].),
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].)
]
# Table: district
[
  (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
  (A4, number of inhabitants . Value examples: ['95907', '95616', '94812'].),
  (A11, average salary. Value examples: [12541, 11277, 8114, 8110, 8814].)
]
【Foreign keys】
account.`district_id` = district.`district_id`
client.`district_id` = district.`district_id`
【Question】
What is the gender of the youngest client who opened account in the lowest average salary branch?
【Evidence】
Later birthdate refers to younger age; A11 refers to average salary

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
Sub question 1: What is the district_id of the branch with the lowest average salary?
SQL
```sql
SELECT `district_id`
  FROM district
  ORDER BY `A11` ASC
  LIMIT 1
```

Sub question 2: What is the youngest client who opened account in the lowest average salary branch?
SQL
```sql
SELECT T1.`client_id`
  FROM client AS T1
  INNER JOIN district AS T2
  ON T1.`district_id` = T2.`district_id`
  ORDER BY T2.`A11` ASC, T1.`birth_date` DESC 
  LIMIT 1
```

Sub question 3: What is the gender of the youngest client who opened account in the lowest average salary branch?
SQL
```sql
SELECT T1.`gender`
  FROM client AS T1
  INNER JOIN district AS T2
  ON T1.`district_id` = T2.`district_id`
  ORDER BY T2.`A11` ASC, T1.`birth_date` DESC 
  LIMIT 1 
```
Question Solved.

==========

【Database schema】
{desc_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}

Decompose the question into sub questions, considering 【Constraints】, and generate the SQL after thinking step by step:
"""


zeroshot_template = """
Given a 【Database schema】 description, a knowledge 【Evidence】 and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then generate SQL.
You can write answer in script blocks, and indicate script type in it, like this:
```sql
SELECT column_a
FROM table_b
```
When generating SQL, we should always consider constraints:
【Constraints】
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values

Now let's start!

【Database schema】
{desc_str}
【Foreign keys】
{fk_str}
【Question】
{query}
【Evidence】
{evidence}
【Answer】
"""


baseline_template = """
Given a 【Database schema】 description and the 【Question】, you need to use valid SQLite and understand the database and knowledge, and then generate SQL.
You can write answer in script blocks, and indicate script type in it, like this:
```sql
SELECT column_a
FROM table_b
```

【Database schema】
{desc_str}
【Question】
{query}
【Answer】
"""


soft_refiner_template = """
【Instruction】
When executing SQL below, some errors occurred, please fix up SQL based on query and database info.
Solve the task step by step if you need to. Using SQL format in the code block, and indicate script type in the code block.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
【Constraints】
- The SQL should start with 'SELECT'
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- If use `JOIN <table>`, the connected columns should be in the Foreign keys of 【Database schema】
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected
【Response format】
Your response should be in this format:
Analysis:
**[Your analysis]**
Correct SQL:
```sql
[the fixed SQL]
```
【Attention】
Only SQL statements are allowed in [the fixed SQL], do not add any comments.

【Query】
{query}
【Evidence】
{evidence}
【Database info】
{desc_str}
【Primary keys】
{pk_str}
【Foreign keys】
{fk_str}
【Detailed descriptions of tables and columns】
{detailed_str}
【old SQL】
```sql
{sql}
```
【SQLite error】 
{sqlite_error}
【Exception class】
{exception_class}

Now please fixup old SQL and generate new SQL again.
【correct SQL】
"""

withoutData_refiner_template = """
【Instruction】
When executing SQL below, some errors occurred, please fix up SQL based on query and database info.
Solve the task step by step if you need to. Using SQL format in the code block, and indicate script type in the code block.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
【Possible error】
When using nested SQL, using the MIN or MAX function in the sub-SQL may result in null data in the end. Because when multiple tables are joined, they are connected by foreign keys and contain only some data in common, the maximum or minimum value of a column in a table may not be in the joined table.
【Constraints】
- The SQL should start with 'SELECT'
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use `JOIN <table>`, the connected columns should be in the Foreign keys of 【Database schema】
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected
- There are columns with similar names but different meanings, you can find the most accurate columns in the right table based on the 【Summary of each table】
【Response format】
Your response should be in this format:
Analysis:
**[Your analysis]**
Correct SQL:
```sql
[the fixed SQL]
```
【Attention】
Only SQL statements are allowed in [the fixed SQL], do not add any comments.
【Typical examples】
For the error called "no data selected", here are some typical example.
1. Wrong SQL: 
```
SELECT T1.`date` FROM recordtime AS T1 INNER JOIN information AS T2 ON T1.`id` = T2.`id` WHERE T2.`viewers` = ( SELECT MAX(`viewers`) FROM information)
```
Analysis: **Using the MAX function in a nested SQL statement will result in a mismatch because the maximum or minimum value of the column may not be in the joined table, so use `ORDER BY`!**
Correct SQL:
```sql
SELECT T1.`date`
  FROM recordtime AS T1
  INNER JOIN information AS T2
  ON T1.`id` = T2.`id`
  ORDER BY T2.`viewers` DESC 
  LIMIT 1
```
2. Wrong SQL: 
```
SELECT T1.`idea` FROM work AS T1 INNER JOIN student AS T2 ON T1.`ID` = T2.`ID` WHERE T2.`final_score` = ( SELECT MIN(`final_score`) FROM student)
```
Analysis: **Using the MIN function in a nested SQL statement will result in a mismatch because the maximum or minimum value of the column may not be in the joined table, so use `ORDER BY`!**
Correct SQL:
```sql
SELECT T1.`idea`
  FROM work AS T1
  INNER JOIN student AS T2
  ON T1.`ID` = T2.`ID`
  ORDER BY T2.`final_score` ASC 
  LIMIT 1
```

Here is a new case for you.
【Evidence】
{evidence}
【Query】
-- {query}
【Database info】
{desc_str}
【Primary keys】
{pk_str}
【Foreign keys】
{fk_str}
【Detailed descriptions of tables and columns】
{detailed_str}
【Matched values】
{matched_content}
【old SQL】
```sql
{sql}
```
【SQLite error】 
{sqlite_error}
【Exception class】
{exception_class}

Now please fixup old SQL and generate new SQL again.
【correct SQL】
"""

noFunction_refiner_template = """
【Instruction】
When executing SQL below, some errors occurred, please fix up SQL based on query and database info.
Solve the task step by step if you need to. Using SQL format in the code block, and indicate script type in the code block.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
【Possible error】
When the error "no such function" occurs, 【Evidence】 often provides a calculation formula, but the calculation formula often provides a non SQLite function. Prioritize 【Evidence】 and change the function to SQLite function.
【Constraints】
- The SQL should start with 'SELECT'
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- If use `JOIN <table>`, the connected columns should be in the Foreign keys of 【Database schema】
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected
- There are columns with similar names but different meanings, you can find the most accurate columns in the right table based on the 【Summary of each table】
【Response format】
Your response should be in this format:
Analysis:
**[Your analysis]**
Correct SQL:
```sql
[the fixed SQL]
```
【Attention】
Only SQL statements are allowed in [the fixed SQL], do not add any comments.
【Typical examples】
For the error called "no such function", here are some typical example.
1. Query: What is the average monthly number of links created in 2010 for posts that have no more than 2 answers?
Evidence: calculation = DIVIDE(COUNT(Id where YEAR(CreationDate) = 2010 and AnswerCount < = 2), 12)
old SQL: 
```
SELECT DIVIDE(COUNT(T1.Id), 12) 
  FROM postLinks AS T1 
  INNER JOIN posts AS T2 ON T1.PostId = T2.Id
  WHERE YEAR(T1.`CreationDate`) = '2010' AND T2.AnswerCount <= 2
```
SQLite error: no such function: DIVIDE
Analysis: ** Prioritize evidence. The evidence shows that calculation=DIVIDE (COUNT (Id where YEAR (CreationDate)=2010 and AnswerCount<=2), 12) However, the DIVIDE function and the YEAR function are not supported in SQLite. To fix old SQL, first replace DIVIDE with / to perform division, and use CAST(COUNT(T1.Id) AS REAL) to ensure the division result is a floating-point number (to avoid integer division when dividing by 12). Then replace YEAR(T1.CreationDate) with STRFTIME('%Y', T1.CreationDate) to extract the year. **
Correct SQL:
```sql
SELECT CAST(COUNT(T1.Id) AS REAL) / 12 
FROM postLinks AS T1 
INNER JOIN posts AS T2 ON T1.PostId = T2.Id
WHERE T2.AnswerCount <= 2 AND STRFTIME('%Y', T1.CreationDate) = '2010'
```
2. Query: How old is the youngest Japanese driver? What is his name?
Evidence: date of birth refers to drivers.dob; The larger the birthday value, the younger the person is, and vice versa; Japanese refers to nationality = 'Japanese'; age = YEAR(CURRENT_TIMESTAMP) - YEAR(dob);
old SQL: 
```
SELECT MIN(YEAR(CURRENT_TIMESTAMP) - YEAR(dob)) AS age, forename, surname
  FROM drivers
  WHERE dob = (
    SELECT MIN(dob)
    FROM drivers
    WHERE nationality = 'Japanese'
  )
```
SQLite error: no such function: YEAR
Analysis: ** Prioritize evidence. The evidence shows that age=YEAR (CURRENT_TIMESTAMP) - YEAR (dob), but the YEAR function is not supported in SQLite. To fix old SQL, the first step is to replace the unsupported YEAR function with STRFTIME('%Y', ...) to extract the year from a date in SQLite, and use CAST to convert the year extracted from STRFTIME into an integer for performing arithmetic calculations. And the evidence also suggests that the larger the birthday value, the younger the person is. Therefore, the use of MIN(dob) in the subquery is redundant because the youngest person can be directly identified using the ORDER BY and LIMIT clauses. Instead of the subquery, directly use ORDER BY age ASC to sort the drivers by age, and include NULLS LAST in the ORDER BY clause to ensure rows with NULL values for dob do not interfere with the sorting. Finally, add LIMIT 1 to select only the youngest driver. **
Correct SQL:
```sql
SELECT (CAST(STRFTIME('%Y', 'now') AS INTEGER) - CAST(STRFTIME('%Y', dob) AS INTEGER)) AS age, forename, surname
FROM drivers
WHERE nationality = 'Japanese'
ORDER BY age ASC NULLS LAST
LIMIT 1
```

Here is a new case for you.
【Query】
{query}
【Evidence】
{evidence}
【Database info】
{desc_str}
【Primary keys】
{pk_str}
【Foreign keys】
{fk_str}
【Detailed descriptions of tables and columns】
{detailed_str}
【Matched values】
{matched_content}
【old SQL】
```sql
{sql}
```
【SQLite error】 
{sqlite_error}
【Exception class】
{exception_class}

Now please fixup old SQL and generate new SQL again.
【correct SQL】
"""

syntaxError_refiner_template = """
【Instruction】
When executing SQL below, syntax errors occurred, please fix up SQL based on query, evidence and database info.
When a syntax error occurs, it is often accompanied by other errors such as column selection errors or calculation errors. You need to reanalyze the 【old SQL】to ensure that the SQL statement accurately reflects the 【Query】and 【Evidence】, and review the query logic reasonably based on the 【Database info】. If there are no column selection errors or calculation errors, you only need to modify the syntax error in the response, otherwise modify the old SQL to what you think is the correct 【correct SQL】.
Solve the task step by step if you need to. Using SQL format in the code block, and indicate script type in the code block.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
【Constraints】
- The SQL should start with 'SELECT'
- In `SELECT <column>`, just select needed columns in the 【Question】 without any unnecessary column or value
- In `FROM <table>` or `JOIN <table>`, do not include unnecessary table
- If use max or min func, `JOIN <table>` FIRST, THEN use `SELECT MAX(<column>)` or `SELECT MIN(<column>)`
- If [Value examples] of <column> has 'None' or None, use `JOIN <table>` or `WHERE <column> is NOT NULL` is better
- If use `ORDER BY <column> ASC|DESC`, add `GROUP BY <column>` before to select distinct values
- If use `JOIN <table>`, the connected columns should be in the Foreign keys of 【Database schema】
- If use `ORDER BY <column> ASC LIMIT <n>`, please use `ORDER BY <column> ASC NULLS LAST LIMIT <n>` to make sure the null values will not be selected
- There are columns with similar names but different meanings, you can find the most accurate columns in the right table based on the 【Summary of each table】
【Response format】
Your response should be in this format:
Analysis:
**[Your analysis]**
Correct SQL:
```sql
[the fixed SQL]
```
【Attention】
Only SQL statements are allowed in [the fixed SQL], do not add any comments.

【Query】
{query}
【Evidence】
{evidence}
【Database info】
{desc_str}
【Primary keys】
{pk_str}
【Foreign keys】
{fk_str}
【Detailed descriptions of tables and columns】
{detailed_str}
【Matched values】
{matched_content}
【old SQL】
```sql
{sql}
```
【SQLite error】 
{sqlite_error}
【Exception class】
{exception_class}

Now please fixup old SQL and generate new SQL again.
【correct SQL】
"""