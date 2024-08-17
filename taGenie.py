from mngDB import MngDB
from schemeAnnotator import SchemeAnnotator
from taskGen import TaskGen
from kpiGen import KPIGen
from sqlGen import SQLGen
from sqlChecker import SQLChecker
from userReport import UserReport
from visGen import VisGen
import logging

class TAGenie:
    def __init__(self): pass
    def generate_use_case(self, use_case): return self.generate_analytics(use_case['user'],use_case['org'])
    def generate_analytics(self,user_info, org_info):
        user_info=self.provision_user(user_info,org_info)
        self.prepare_schema(user_info['user_org_uid'])
        self.generate_tasks(user_info['user_uid'])
        self.generate_kpis(user_info['user_uid'])
        self.generate_queries(user_info['user_uid'])
        self.test_queries(user_info['user_uid'])
        self.print_user_report(user_info['user_uid'])
        self.attempt_fix_sqls(user_info['user_uid'])
        self.generate_visuals(user_info['user_uid'])
        self.print_user_report(user_info['user_uid'])
        
    def provision_user(self,user_info,org_info): 
        logging.info(f"\n============================ starting provisioning of user and his org=======================================================\n")
        return MngDB().create_or_update_user(user_info, org_info)
    
    def prepare_schema(self, org_uid): 
        logging.info(f"\n============================ fetching and annotating DB scheme=======================================================\n")
        return SchemeAnnotator().prepare_schema(org_uid)
    
    def generate_tasks(self, user_uid): 
        logging.info(f"\n============================ generate user responsibilities and tasks =======================================================\n")
        return TaskGen().generate_user_tasks(user_uid)
    
    def generate_kpis(self,user_uid): 
        logging.info(f"\n============================ generating user KPIs =======================================================\n")
        return KPIGen().generate_user_kpis(user_uid)
    
    def generate_queries(self, user_uid): 
        #return SQLGen().generate_kpis_sql(user_uid)
        logging.info(f"\n============================ generating KPI SQL queries =======================================================\n")
        return SQLGen().generate_kpis_sql_raw(user_uid)
    
    def test_queries(self, user_uid): 
        logging.info(f"\n============================ testing KPI SQL queries =======================================================\n")
        return SQLChecker().test_kpis(user_uid)
    
    def print_user_report(self,user_uid):
        logging.info(f"\n============================ reporting KPI and data stats =======================================================\n")
        return  UserReport().print_user_stats(user_uid)
    
    def attempt_fix_sqls(self,user_uid):
        logging.info(f"\n============================ attempting to debug and fix queries =======================================================\n")
        return SQLGen().attempt_fix_sqls(user_uid)
    
    def generate_visuals(self,user_uid):
        logging.info(f"\n============================ generating visuals =======================================================\n")
        return VisGen().generate_user_visuals(user_uid)
        
        