# -*- coding: utf-8 -*-
from core.utils import parse_json, parse_sql_from_string, add_prefix, load_json_file, extract_world_info, is_email, \
    is_valid_date_column, parse_category, extract_sql
from func_timeout import func_set_timeout, FunctionTimedOut, func_timeout

LLM_API_FUC = None
# try import core.api, if error then import core.llm
try:
    from core import api
    LLM_API_FUC = api.safe_call_llm
    print(f"Use func from core.api in agents.py")
except:
    from core import llm
    LLM_API_FUC = llm.safe_call_llm
    print(f"Use func from core.llm in agents.py")

from core.const import *
from typing import List
from copy import deepcopy

import sqlite3
import time
import abc
import sys
import os
import glob
import pandas as pd
from tqdm import tqdm, trange
from pprint import pprint
import pdb
import tiktoken


class BaseAgent(metaclass=abc.ABCMeta):
    def __init__(self):
        pass

    @abc.abstractmethod
    def talk(self, message: dict):
        pass

class Error_Driven_Refiner(BaseAgent):
    """
    Refiner for SQL refine
    """
    name = ERROR_DRIVEN_REFINER_NAME
    description = "Execute SQL and preform validation"

    def __init__(self, data_path: str, dataset_name: str):
        super().__init__()
        self.data_path = data_path
        self.dataset_name = dataset_name
        self._message = {}

    def run_sql(self,sql: str, db_id: str):
        db_path = f"{self.data_path}/{db_id}/{db_id}.sqlite"
        conn = sqlite3.connect(db_path)
        conn.text_factory = lambda b: b.decode(errors="ignore")
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        return result

    def _execute_sql(self, sql: str, db_id: str) -> dict:
        try:
            result = func_timeout(30,self.run_sql,args=(sql,db_id))
            return {
                "sql": str(sql),
                "data": result[:5],
                "sqlite_error": "",
                "exception_class": ""
            }
        except FunctionTimedOut as te:
            return {
                "sql": str(sql),
                "sqlite_error": str(te.args),
                "exception_class": str(type(te).__name__)
            }
        except sqlite3.Error as er:
            return {
                "sql": str(sql),
                "sqlite_error": str(' '.join(er.args)),
                "exception_class": str(er.__class__)
            }
        except Exception as e:
            return {
                "sql": str(sql),
                "sqlite_error": str(e.args),
                "exception_class": str(type(e).__name__)
            }


    def _is_need_refine(self, exec_result: dict, try_times: int):
        # if Spider set, allow return None value
        if self.dataset_name == 'spider':
            if 'data' not in exec_result:
                return True
            return False

        data = exec_result.get('data', None)
        if try_times >= 2:
            return False
        if data is not None:
            if len(data) == 0:
                exec_result['sqlite_error'] = 'no data selected'
                return True
            if len(data) == 1:
                return False
            check_all_None = True
            check_None = False
            for t in data:
                for n in t:
                    if n is None:
                        exec_result['sqlite_error'] = 'None value existed'
                        check_None = True
                    else:
                        check_all_None = False
            if check_None and not check_all_None:
                # There are NULL values but not all values are null
                return True
            return False
        else:
            return True

    def _refine(self,
               query: str,
               evidence:str,
               schema_info: str,
               complete_schema: str,
               pk_info: str,
               column_details: str,
               fk_info: str,
               error_info: dict,
               matched_content: str) -> dict:
        sql_arg = add_prefix(error_info.get('sql'))
        sqlite_error = error_info.get('sqlite_error')
        exception_class = error_info.get('exception_class')
        if "no such column" in sqlite_error.lower():
            sqlite_error = sqlite_error + " (Check if the column in the SQL is selected from the correct table based on the 【Database info】 at first, and then check if the column name is enclosed in backticks.)"
            prompt = soft_refiner_template.format(query=query, evidence=evidence, desc_str=complete_schema, \
                                             pk_str=pk_info, detailed_str=column_details, fk_str=fk_info, \
                                             sql=sql_arg, sqlite_error=sqlite_error, \
                                             exception_class=exception_class)
        elif "no data selected" in sqlite_error.lower() and sql_arg.count('SELECT') > 1:
            prompt = withoutData_refiner_template.format(query=query, evidence=evidence, desc_str=schema_info, \
                                                    pk_str=pk_info, detailed_str=column_details, fk_str=fk_info, \
                                                    sql=sql_arg, sqlite_error=sqlite_error,
                                                    matched_content=matched_content, \
                                                    exception_class=exception_class)
        elif "None value existed" in sqlite_error:
            sqlite_error = sqlite_error + ", you can add `IS NOT NULL` in SQL"
            prompt = soft_refiner_template.format(query=query, evidence=evidence, desc_str=schema_info, \
                                             pk_str=pk_info, detailed_str=column_details, fk_str=fk_info, \
                                             sql=sql_arg, sqlite_error=sqlite_error, \
                                             exception_class=exception_class)
        elif "syntax error" in sqlite_error.lower():
            sqlite_error = sqlite_error + " (Check the reason for the syntax errors in SQL at first, and then determine the correction method to make the necessary changes.)"
            prompt = soft_refiner_template.format(query=query, evidence=evidence, desc_str=schema_info, \
                                             pk_str=pk_info, detailed_str=column_details, fk_str=fk_info, \
                                             sql=sql_arg, sqlite_error=sqlite_error, \
                                             exception_class=exception_class)
        elif "no such function" in sqlite_error.lower():
            sqlite_error = sqlite_error + " (Check if the calculations in SQL are based on 【Evidence】 at first, and then check if the function conforms to SQLite's function.)"
            prompt = soft_refiner_template.format(query=query, evidence=evidence, desc_str=schema_info, \
                                             pk_str=pk_info, detailed_str=column_details, fk_str=fk_info, \
                                             sql=sql_arg, sqlite_error=sqlite_error, \
                                             exception_class=exception_class)
        else:
            prompt = soft_refiner_template.format(query=query, evidence=evidence, desc_str=schema_info, \
                                             pk_str=pk_info, detailed_str=column_details, fk_str=fk_info, \
                                             sql=sql_arg, sqlite_error=sqlite_error, \
                                             exception_class=exception_class)

        word_info = extract_world_info(self._message)
        reply = LLM_API_FUC(prompt, **word_info)
        res = extract_sql(reply)
        return res

    def talk(self, message: dict):
        if message['send_to'] != self.name: return
        self._message = message
        db_id, old_sql, query, evidence, schema_info, fk_info, complete_schema  = message.get('db_id'), \
                                                            message.get('pred', message.get('final_sql')), \
                                                            message.get('query'), \
                                                            message.get('evidence'), \
                                                            message.get('desc_str'), \
                                                            message.get('fk_str'), \
                                                            message.get('complete_desc_str')
        pk_info = message.get('pk_str')
        column_details = message.get('columns_details_str')
        if self.dataset_name == 'bird':
            if message.get('matched_list') != []:
                matched_content = '; '.join(message.get('matched_list'))
            else:
                matched_content = 'No matched values.'
        else:
            matched_content = 'No matched values.'

        # column_details = message.get('columns_details_str')
        if 'error' in old_sql:
            message['try_times'] = 0
            message['send_to'] = LOGIC_DRIVEN_DECOMPOSER_NAME
            message['pred'] = old_sql
            return

        error_info = self._execute_sql(old_sql, db_id)
        try_times = message.get('try_times', 0)
        need_refine = self._is_need_refine(error_info, try_times)
        if not need_refine:  # correct in one pass or refine success
            if ' || \' \' || ' in old_sql:
                old_sql = old_sql.replace(' || \' \' || ', ', ')
            old_sql = old_sql.replace('ASC LIMIT', 'ASC NULLS LAST LIMIT')
            # print("Final predicted sql: ", old_sql)
            message['try_times'] = message.get('try_times', 0) + 1
            message['pred'] = old_sql
            message['send_to'] = SYSTEM_NAME

        else:
            # need refine SQL
            new_sql = self._refine(query, evidence, schema_info, complete_schema, pk_info, column_details, fk_info, error_info, matched_content)
            message['try_times'] = message.get('try_times', 0) + 1
            message['pred'] = new_sql
            message['fixed'] = True
            message['send_to'] = ERROR_DRIVEN_REFINER_NAME
        return


if __name__ == "__main__":
    m = 0